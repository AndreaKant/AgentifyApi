import json
from .llm_api import call_llm

LLM_STRATEGIST = "gemini-2.5-pro"

class StrategicPlanner:
    def create_strategic_plan(self, user_query, available_tools_summary, context):
        prompt = f"""
        Sei un **Architetto di Soluzioni AI iper-efficiente**. Il tuo unico compito è tradurre una richiesta utente in un piano d'azione JSON **logico, diretto e senza passaggi inutili**.

        **Richiesta Utente:** "{user_query}"
        **Strumenti Disponibili (Nome e Descrizione):** 
        {json.dumps(available_tools_summary, indent=2)}

        ---
        **REGOLE DI PENSIERO CRITICO (SEGUILE ALLA LETTERA):**

        1.  **PRINCIPIO DI MINIMA AZIONE:** Non creare step per ottenere informazioni che sono già fornite da uno step precedente. Se `GetUser` restituisce l'utente E il suo stato di attività, il piano deve fermarsi lì. **Non aggiungere uno step "Verifica lo stato di attività"**. È ridondante.

        2.  **VALIDAZIONE DELLA CATENA DI DATI:** Assicurati che ogni step sia fattibile. Non creare un obiettivo come "Trova l'email dall'ordine" se sai che lo strumento `get_order_details` non restituisce l'email. Il piano corretto in quel caso è: `["Trova ordine X", "Usa l'ID utente dall'ordine per trovare l'utente Y"]`.

        3.  **DISAMBIGUAZIONE PROATTIVA:** Se un termine nella richiesta è ambiguo (es. "stato"), controlla le descrizioni degli strumenti. Se "stato" può riferirsi sia a un ordine che a un utente, crea un piano che li ottenga entrambi se necessario o che chieda chiarimenti.

        **REGOLE DI FORMATTAZIONE:**
        - Ogni obiettivo deve essere una frase CORTA e DIRETTA.
        - Ogni obiettivo deve descrivere UNA SOLA chiamata di strumento.
        - Ogni obiettivo deve fornire tutte le indicazioni chiave per ottenere quello che serve avendo come dati di partenza il risultato dello step precedente
        - Rispondi ESCLUSIVAMENTE con un oggetto JSON con una chiave "plan".

        ---
        **ESEMPIO DI PIANO PERFETTO:**
        Richiesta: "Qual è l'email dell'autore dell'ultima recensione e lo stato del suo ultimo ordine?"
        {{
            "plan": [
                "Cerca tutte le recensioni",
                "Cerca i dettagli dell'utente che ha scritto l'ultima recensione dai dati precedenti",
                "Usa sempre lo stesso ID utente per cercare l'elenco dei suoi ordini"
            ]
        }}
        """
        response_str = call_llm(LLM_STRATEGIST,prompt,is_json_output=True)
        return json.loads(response_str)