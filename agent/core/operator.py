import json
from .llm_api import call_llm

def execute_task_and_prepare_call(task_description, context_results, relevant_functions, model_to_use):
    """LLM Operativo: sceglie un tool per un singolo task, usando i risultati precedenti."""
    
    tools_prompt_string = "" # ... (codice identico a choose_and_prepare...)
    for metadata, contract in relevant_functions:
        tools_prompt_string += f"--- Strumento ---\nMetadati: {json.dumps(metadata)}\nContratto: {contract.strip()}\n-----------------\n"

    print(f"   📊 Dati disponibili per questo step: {list(context_results.keys())}")

    user_provided_info = {}
    for key, value in context_results.items():
        if "user_info" in key:
            user_provided_info[key] = value
            
    system_prompt = """
    Sei un AI operativo. Il tuo unico compito è eseguire un singolo task specifico.
    Ti vengono forniti: un obiettivo, una lista di strumenti e i dati ottenuti dagli step precedenti.

    **REGOLA FONDAMENTALE SUI DATI:**
    I dati dagli step precedenti sono la tua unica fonte di verità. Se il task dice "usa l'ID utente ottenuto nello step 1", devi cercare nei "Dati Disponibili" la chiave "step_1_result" e al suo interno il campo corretto (es. "userId").
    **NON chiedere all'utente informazioni che potrebbero già essere presenti nei dati disponibili.**

    **ESEMPIO di payload corretto:**
    Se il task dice "Recupera dettagli dell'ordine 'ord-002'" e lo strumento ha path "/orders/{order_id}", 
    il payload deve essere: {"order_id": "ord-002"}

    Se il task dice "Trova l'utente con ID 5" e lo strumento richiede un campo "id",
    il payload deve essere: {"id": 5}

    **REGOLA DI SANITY CHECK:**
    Se l'obiettivo che ti viene assegnato sembra illogico o impossibile da eseguire con gli strumenti e i dati forniti, non tentare di forzare una chiamata. Invece, usa l'azione "ask_user" per segnalare il problema.
    Esempio: Obiettivo="Estrai l'email dell'ordine", Dati={"step_1_result": {"orderId": "..."}}. Se vedi che lo strumento per gli ordini non fornisce email, chiedi: "Non posso estrarre un'email da un ordine. Devo invece cercare l'utente associato a quest'ordine?"

    **FORMATO DI RISPOSTA:**
    Rispondi SOLO con un JSON con la struttura:
    {
    "action": "call_tool",
    "tool_metadata": { ... },
    "payload": { ... }
    }
    OPPURE
    {
    "action": "ask_user",
    "question": "La tua domanda specifica per l'utente o la tua segnalazione del problema."
    }
    OPPURE se hai già tutti i dati necessari per rispondere:
    {
        "action": "provide_answer",
        "answer": "La risposta diretta basata sui dati disponibili"
    }
    OPPURE se ti accorgi che servono step intermedi:
    {
        "action": "suggest_additional_step",
        "reasoning": "L'ordine non contiene l'email, devo prima trovare l'utente",
        "new_step": "Trova i dettagli dell'utente con ID ${step_1_result.userId}"
    }

    
    Puoi opzionalmente specificare quali campi ti servono dalla risposta:
    {
        "action": "call_tool",
        "tool_metadata": { ... },
        "payload": { ... },
        "extract_fields": ["campo1", "campo2.sottocampo", "array[].campo"]
    }
    """
    
    human_prompt = f"""
**Obiettivo da Eseguire:** 
"{task_description}"

**Dati Disponibili dagli Step Precedenti (se ti servono):**
{json.dumps(context_results, indent=2, ensure_ascii=False)}

**Strumenti Rilevanti per questo Obiettivo:**
{tools_prompt_string}

Analizza l'obiettivo, prendi i dati che ti servono e scegli UN solo strumento per eseguirlo. Prepara il payload.
"""
    print("🤖 Chiedo all'LLM operativo di scegliere lo strumento...")
    try:
        response_str = call_llm(model_to_use, f"{system_prompt}\n\n---\n\n{human_prompt}", is_json_output=True)
        
        print("   -> LLM ha risposto.")
        return json.loads(response_str) # Converti la stringa JSON in un dizionario Python
    except Exception as e:
        print(f"❌ Errore durante la chiamata all'LLM: {e}")
        return {"error": "Errore interno durante la preparazione dello strumento."}