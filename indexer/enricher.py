LLM_ENRICHER_MODEL = "gemini-2.5-pro"

def enrich_api_function(api_function: dict, call_llm_func) -> str:
    """
    Usa un LLM per analizzare un contratto API e generare una descrizione
    dettagliata e utile per l'agente.
    """
    func_type = api_function.get("type")
    contract = api_function.get("source_contract")
    original_description = api_function.get("description", "")
    
    prompt = f"""
    Sei un Analista di API esperto. Il tuo compito è creare una descrizione concisa ma super-dettagliata per una funzione API, in modo che un agente AI possa capirne esattamente l'uso, i parametri e le limitazioni.

    API da analizzare:
    - Tipo: {func_type}
    - Descrizione Originale (se presente): "{original_description}"
    - Contratto Tecnico:
    ---
    {contract}
    ---

    Analizza il contratto e la descrizione originale. Poi, genera una nuova descrizione migliorata che INCLUDa:
    1.  **Scopo Principale:** A cosa serve la funzione in una frase.
    2.  **Parametri Chiave:** Quali sono i parametri più importanti e cosa rappresentano (es. `productId` è l'ID univoco di un prodotto).
    3.  **Dati Restituiti:** Quali sono i campi più importanti che restituisce.
    4.  **Limitazioni o Comportamenti Specifici:** Ad esempio, se `searchProducts` cerca solo nel nome e nella descrizione, DEVI specificarlo chiaramente. Se una funzione richiede un ID specifico (es. `warehouseId`), menzionalo.
    
    **Esempio di output per `searchProducts`:**
    "Cerca prodotti nel catalogo tramite una query a testo libero. Cerca SOLO nel nome e nella descrizione del prodotto, non nelle varianti o nei fornitori. Restituisce una lista di prodotti con id, nome e descrizione."

    **Esempio di output per `warehouseStock`:**
    "Recupera i livelli di inventario per tutti i prodotti in un magazzino specifico. Richiede l'ID univoco del magazzino (`warehouseId`) come parametro. Restituisce una lista di oggetti StockLevel."
    
    Fornisci solo e unicamente il testo della nuova descrizione. Non aggiungere titoli o testo introduttivo.
    """
    
    print(f"   -> 🧠 Arricchimento LLM per '{api_function['name']}'...")
    
    # Chiamiamo l'LLM senza aspettarci un JSON
    new_description = call_llm_func(LLM_ENRICHER_MODEL, prompt, is_json_output=False)
    
    # Semplice pulizia da eventuali virgolette extra che l'LLM potrebbe aggiungere
    if new_description.startswith('"') and new_description.endswith('"'):
        new_description = new_description[1:-1]
        
    return new_description.strip()