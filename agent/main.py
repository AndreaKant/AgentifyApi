# FILE: agent/main.py
import json
from psycopg2.extras import RealDictCursor

# --- Import moduli ---
from .core.planner import StrategicPlanner
from .core.operator import execute_task_and_prepare_call
from .recovery_agent import RecoveryAgent
from .utils import find_most_relevant_functions, resolve_payload_variables
from utils.llm_api import call_llm
from .core.session_manager import session_manager
from .tools.executors import execute_tool

# --- Import utility condivise ---
from utils.database import get_db_connection
from utils.embeddings import get_embedding

# --- Costanti dei Modelli ---
LLM_ADVANCED_OPERATOR = "gemini-2.5-pro"
LLM_SIMPLE_OPERATOR = "gemini-2.5-pro"
LLM_SYNTHESIZER = "gemini-2.5-pro"

def main():
    """Il loop principale che orchestra l'agente."""
    print("🤖 Salve! Sono un Agente Ibrido V2. Come posso aiutarti?")
    conn = get_db_connection()
    conversation_history = []

    while True:
        chain_results = {}
        user_query = input("\n> ")
        if not user_query.strip(): continue
        if user_query.lower() == 'esci': break
        conversation_history.append({"role": "user", "content": user_query})
        
        # 1. PIANIFICAZIONE STRATEGICA
        print("\n\033[95m🧠 [STRATEGA]\033[0m Creando un piano con GPT-4 Turbo...")
        query_embedding = get_embedding(user_query)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT metadata, source_contract FROM api_functions ORDER BY embedding <=> %s::vector LIMIT 7", (str(query_embedding),))
            relevant_functions_raw = cur.fetchall()

        tools_summary = [{"name": r['metadata'].get("name"), "description": r['source_contract'][:150]} for r in relevant_functions_raw]

        planner = StrategicPlanner()
        strategic_plan_json = planner.create_strategic_plan(user_query, tools_summary, conversation_history)
        plan = strategic_plan_json.get("plan", [])
        
        print("\033[95m🗺️  [STRATEGA]\033[0m Piano strategico generato:")
        print(json.dumps(plan, indent=2, ensure_ascii=False))

        # 2. ESECUZIONE DEL PIANO
        execution_success = True
        recovery_agent = RecoveryAgent(user_query=user_query, full_plan=plan)
        i = 0
        while i < len(plan):
            task = plan[i]
            task_description = task
            print(f"\n\033[94m📍 [ESECUTORE]\033[0m Step {i+1}/{len(plan)}: {task_description}")

            task_embedding = get_embedding(task_description)
            with conn.cursor() as cur:
                cur.execute("SELECT metadata, embedding <=> %s::vector AS distance FROM api_functions ORDER BY distance LIMIT 1", (str(task_embedding),))
                best_match = cur.fetchone()
            
            is_complex_context_task = i > 0
            distance = best_match[1] if best_match else 1.0

            if is_complex_context_task or distance > 0.45:
                model_for_operator = LLM_ADVANCED_OPERATOR
                print(f"   - 🧠 Routing a: {LLM_ADVANCED_OPERATOR} (Task complesso o distanza alta)")
            else:
                model_for_operator = LLM_SIMPLE_OPERATOR
                print(f"   - 🧠 Routing a: {LLM_SIMPLE_OPERATOR} (Task semplice e diretto)")

            task_relevant_functions = find_most_relevant_functions(
                task_description,
                user_query, conn, top_k=3)
            
             # --- LOGGING AGGRESSIVO PER L'OPERATIVO ---
            print(f"\033[94m   🤖 [OPERATIVO]\033[0m Chiamata a {model_for_operator} con i seguenti dati:")
            print("\033[90m      --- INIZIO CONTESTO PER OPERATIVO ---")
            print(f"      OBIETTIVO: {task_description}")
            print(f"      DATI DISPONIBILI: {json.dumps(chain_results, indent=2, ensure_ascii=False)}")
            print(f"      STRUMENTI RILEVANTI: {[func.get('metadata', {}).get('name') for func in task_relevant_functions]}")
            print("      --- FINE CONTESTO PER OPERATIVO ---\033[0m")
            # ---------------------------------------------
            
            prepared_tool_call = execute_task_and_prepare_call(
                task_description, chain_results, task_relevant_functions, model_for_operator
            )
            print(f"   🔍 Tool call preparata: {json.dumps(prepared_tool_call, indent=2)}")
            
            action = prepared_tool_call.get("action")
            if action == "call_tool":
                prepared_tool_call["payload"] = resolve_payload_variables(prepared_tool_call.get("payload", {}), chain_results)
                result = recovery_agent.run(
                    tool_call=prepared_tool_call,
                    chain_results=chain_results,
                    current_task=task_description
                )
                
                if result.get("success"):
                    step_output_name = f"step_{i+1}_result"
                    chain_results[step_output_name] = result.get("data")
                    print(f"\033[92m   ✅ Step completato. Risultato salvato: {json.dumps(result.get('data'), ensure_ascii=False, indent=2)}\033[0m")
                else:
                    if result.get("strategy") == "request_login":
                        print("🔒 L'agente ha bisogno di autenticarsi. Avvio del flusso di login.")
                        
                        username = input("👤 Inserisci il tuo username: ")
                        password = input("🔑 Inserisci la tua password: ")

                        login_tool_call = {
                            "tool_metadata": {
                                "type": "rest",
                                "base_url": "http://rest_server:8001",
                                "path_template": "/login",
                                "method": "POST"
                            },
                            "payload": {"username": username, "password": password}
                        }
                        login_result = execute_tool(login_tool_call)

                        if login_result.get("success") and "access_token" in login_result.get("data", {}):
                            token = login_result["data"]["access_token"]
                            session_manager.set_token(token)
                            print("✅ Login riuscito! Ora ritento l'operazione originale...")
                            continue
                        else:
                            print("❌ Login fallito. Interruzione del piano.")
                            execution_success = False
                            break
                    elif result.get("is_final_error"):
                        explanation = result.get("explanation")
                        print(f"   ❌ Step fallito in modo definitivo. Spiegazione: {explanation}")
                        chain_results[f"step_{i+1}_error"] = explanation
                    else:
                        print(f"   ❌ Step fallito dopo i tentativi di recupero: {result.get('error')}")
                    execution_success = False
                    break
            
            elif action == "ask_user":
                user_answer = input(f"🤖 {prepared_tool_call.get('question')} \n> ")
                chain_results[f"step_{i+1}_user_info"] = user_answer
                print("   ✅ Informazione acquisita dall'utente.")
                continue

            elif action == "provide_answer":
                chain_results[f"step_{i+1}_result"] = prepared_tool_call.get("answer")
                print(f"   ✅ L'operatore ha fornito direttamente la risposta: {prepared_tool_call.get('answer')}")

            elif action == "suggest_additional_step":
                reasoning = prepared_tool_call.get("reasoning")
                new_step = prepared_tool_call.get("new_step")
                
                print(f"   💡 L'operatore suggerisce uno step intermedio:")
                print(f"      Motivo: {reasoning}")
                print(f"      Nuovo step: {new_step}")
                
                new_step = new_step.replace("${step_1_result.userId}", str(chain_results.get("step_1_result", {}).get("userId", "")))
                
                plan.insert(i, new_step)
                print(f"   ✅ Step intermedio aggiunto al piano. Il piano ora ha {len(plan)} step.")
                
                continue

            i += 1
        
        # 3. SINTESI FINALE
        if chain_results:
            print("\n\033[96m✍️  [SINTETIZZATORE]\033[0m Formulando la risposta finale...")
            
            synthesis_prompt = f"""
            Sei un assistente AI che comunica i risultati finali all'utente.
            La richiesta originale dell'utente era: "{user_query}"

            Il contesto completo dei risultati (e degli errori) ottenuti è:
            {json.dumps(chain_results, indent=2, ensure_ascii=False)}

            Tuo Compito: Formula una risposta finale.
            - Se l'esecuzione è andata a buon fine, riassumi il risultato finale per l'utente.
            - Se c'è stato un errore (cerca una chiave '..._error' in `chain_results`), spiega gentilmente all'utente cosa non ha funzionato, usando la spiegazione fornita.
            - Sii sempre conciso, amichevole e NON inventare MAI informazioni.
            - La tua risposta deve essere una singola stringa di testo puro. NON PRODURRE JSON.
            """
            response_str = call_llm(LLM_SYNTHESIZER, synthesis_prompt, is_json_output=False)
            print(f"\n\033[1m🤖 RISPOSTA FINALE:\033[0m {response_str}")
            conversation_history.append({"role": "assistant", "content": response_str})
        elif not execution_success:
            print("\n--- ⚠️ La Catena è stata interrotta ---")

    conn.close()

if __name__ == '__main__':
    main()