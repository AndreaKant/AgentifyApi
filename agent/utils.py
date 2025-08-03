from utils.embeddings import get_embedding

def find_most_relevant_functions(task_description: str, user_query: str, conn, top_k=5):
    """
    Trova le 'top_k' funzioni più rilevanti nel DB, usando SIA il task
    corrente CHE la query originale dell'utente per un contesto più ricco.
    """
    
    text_to_embed = f"Obiettivo utente: {user_query}\nTask specifico: {task_description}"
    
    query_embedding = get_embedding(text_to_embed)

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT metadata, source_contract, description -- Aggiungi la descrizione
            FROM api_functions 
            ORDER BY embedding <=> %s::vector 
            LIMIT %s
            """,
            (str(query_embedding), top_k)
        )
        results = cur.fetchall()
    
    keys = ["metadata", "source_contract", "description"]
    return [dict(zip(keys, row)) for row in results]

def resolve_payload_variables(payload, context_results):
    """Sostituisce le variabili nel payload con i dati dagli step precedenti."""
    if not isinstance(payload, dict):
        return payload
        
    resolved = {}
    for key, value in payload.items():
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            path_str = value[2:-1]
            resolved[key] = get_nested_value(path_str, context_results)
        else:
            resolved[key] = value
    return resolved

def get_nested_value(path_str, data):
    """Naviga in un dizionario di risultati usando un percorso come 'step_1_result.userId'."""
    path_parts = path_str.split('.')
    current_value = data
    for part in path_parts:
        if isinstance(current_value, dict):
            current_value = current_value.get(part)
        elif isinstance(current_value, list) and part.isdigit():
            try:
                current_value = current_value[int(part)]
            except IndexError:
                return None
        else:
            return None
    return current_value