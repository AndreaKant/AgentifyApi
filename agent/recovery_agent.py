# FILE: agent/recovery_agent.py
import time
import json

from .core.llm_api import call_llm
from .tools.executors import execute_tool  # Assumendo che execute_tool sia qui

LLM_ERROR_ANALYZER = "gemini-1.5-flash-latest"  # Veloce ed economico per l'analisi

class RecoveryAgent:
    """
    Un agente specializzato che implementa un ciclo ReAct per gestire
    e tentare di recuperare da errori durante l'esecuzione di uno strumento.
    """
    def __init__(self, user_query: str, full_plan: list):
        self.user_query = user_query
        self.full_plan = full_plan

    def _classify_error_type(self, error_result: dict) -> str:
        """Classifica l'errore in modo agnostico rispetto al protocollo."""
        error_str = str(error_result.get("error", "")).lower()
        error_data = error_result.get("data", "")

        # REST / HTTP standard
        if "404" in error_str or "not_found" in error_str: return "not_found"
        if "401" in error_str or "403" in error_str or "auth" in error_str: return "auth_error"
        if "400" in error_str or "422" in error_str or "validation" in error_str: return "validation_error"
        if "500" in error_str or "503" in error_str or "unavailable" in error_str: return "server_error"

        # gRPC (basato su testo dell'errore)
        if "unauthenticated" in error_str: return "auth_error"
        
        # GraphQL (controlla la struttura della risposta)
        if isinstance(error_data, dict) and "errors" in error_data:
             return "graphql_error"

        # Generici
        if "timeout" in error_str: return "timeout_error"
        if "connection" in error_str: return "connection_error"
        
        return "unknown_error"

    def _analyze_error_with_llm(self, tool_call: dict, error_result: dict, chain_results: dict, attempt: int, current_task: str) -> dict:
        """Invoca un LLM per analizzare l'errore e scegliere una strategia di recupero."""
        error_type = self._classify_error_type(error_result)
        
        prompt = f"""
        Sei un Dottore di Sistemi AI, un esperto di diagnosi e recupero da errori API.
        
        **CONTESTO DELLA MISSIONE:**
        - Richiesta Originale dell'Utente: "{self.user_query}"
        - Piano d'Azione Completo: {json.dumps(self.full_plan)}
        - Task Corrente Fallito: "{current_task}"
        - Dati Già Raccolti con Successo: {json.dumps(chain_results, indent=2)}

        **PROBLEMA ATTUALE:**
        - Strumento Chiamato: {json.dumps(tool_call.get("tool_metadata"), indent=2)}
        - Tentativo Numero: {attempt + 1}
        - Tipo di Errore Classificato: "{error_type}"
        - Dettagli Errore Ricevuti: {json.dumps(error_result)}

        **STRATEGIE DI RECUPERO DISPONIBILI:**
        1. "retry_with_fix": Se l'errore è un payload palesemente errato e sai esattamente come correggerlo.
        2. "wait_and_retry": Se l'errore sembra temporaneo (es. server_error, timeout_error).
        3. "explain_to_user": Se l'errore è definitivo e non recuperabile (es. not_found, auth_error) e deve essere spiegato all'utente.
        4. "give_up": Come ultima risorsa, se l'errore è incomprensibile o non ci sono alternative.
        
        **DECISIONE:**
        Analizza il problema e rispondi ESCLUSIVAMENTE con un oggetto JSON che descriva la tua strategia.
        
        **Esempi di Risposta JSON:**
        - Per un errore di parametro mancante: 
            {{
                "strategy": "retry_with_fix", 
                "reasoning": "Manca order_id nel payload", 
                "new_payload": {{"order_id": "ord-002"}}  // ESTRAI IL VALORE DAL TASK
            }}
        **- Per un campo inesistente in una query GraphQL:**
            {{
                "strategy": "retry_with_fix",
                "reasoning": "Il campo 'description' non esiste. Rimuovo quel campo dalla stringa della query GraphQL per risolvere il problema.",
                "new_payload": {{
                    "query": "query GetProductById($productId: ID!) {{ getProduct(productId: $productId) {{ id name price inStock }} }}",
                    "variables": {{"productId": "101"}}
                }}
            }}
        - Per un errore di validazione: {{"strategy": "retry_with_fix", "reasoning": "Il rating era 10, ma deve essere <= 5. Lo imposto a 5.", "new_payload": {{"rating": 5, ...}}}}
        - Per un 404: {{"strategy": "explain_to_user", "reasoning": "L'ID richiesto non esiste, non ha senso riprovare.", "explanation": "Mi dispiace, ma sembra che l'elemento che stai cercando non esista. Forse c'è un errore di battitura nell'ID?"}}
        - Per un 503: {{"strategy": "wait_and_retry", "reasoning": "Il server remoto è temporaneamente sovraccarico."}}
        """
        
        analysis_str = call_llm(LLM_ERROR_ANALYZER, prompt, is_json_output=True)
        try:
            return json.loads(analysis_str)
        except json.JSONDecodeError:
            print("   - 💥 L'analizzatore di errori ha prodotto un output non JSON. Fallimento.")
            return {"strategy": "give_up", "reasoning": "L'analizzatore di errori ha prodotto un output non valido."}

    def run(self, tool_call: dict, chain_results: dict, current_task: str, max_retries=3):
        """
        Esegue uno strumento e, in caso di fallimento, orchestra il ciclo ReAct
        di analisi e recupero.
        """

        context = {
            "current_task": current_task,
            "user_query": self.user_query,
            "full_plan": self.full_plan,
            "chain_results": chain_results  # Opzionale ma utile
        }
        
        for attempt in range(max_retries):
            # AZIONE (Act)
            result = execute_tool(tool_call, context)

            if result.get("success"):
                return result  # Successo al primo (o successivo) tentativo!

            # OSSERVAZIONE (Observe)
            print(f"⚠️ Errore rilevato al tentativo {attempt + 1}. Avvio analisi ReAct...")
            
            # PENSIERO (Reason)
            error_analysis = self._analyze_error_with_llm(tool_call, result, chain_results, attempt, current_task)
            strategy = error_analysis.get("strategy")
            reasoning = error_analysis.get('reasoning', 'Nessun ragionamento fornito.')
            
            print(f"   - 🧠 [{strategy.upper()}] {reasoning}")

            # NUOVA AZIONE (Act Again)
            if strategy == "retry_with_fix":
                new_payload = error_analysis.get("new_payload")
                if new_payload:
                    print(f"   - 🔧 Applico fix al payload: {json.dumps(new_payload)}")
                    tool_call["payload"] = new_payload
                    continue
                else:
                    print("   - ❌ Il fix non conteneva un nuovo payload. Interruzione.")
                    break
            
            elif strategy == "wait_and_retry":
                wait_time = 2 ** attempt
                print(f"   - ⏳ Attendo {wait_time}s prima del prossimo tentativo...")
                time.sleep(wait_time)
                continue
            
            elif strategy == "explain_to_user":
                return {"success": False, "is_final_error": True, "explanation": error_analysis.get("explanation")}

            else:  # "give_up" o strategia sconosciuta
                print("   - 🛑 Strategia di recupero non valida o 'give_up'. Interruzione.")
                break

        print("❌ Tutti i tentativi di recupero sono falliti.")
        return result