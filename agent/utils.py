def find_most_relevant_functions(user_query_embedding, conn, top_k=5):
    """Trova le 'top_k' funzioni più rilevanti nel DB usando la ricerca vettoriale."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT metadata, source_contract 
            FROM api_functions 
            ORDER BY embedding <=> %s::vector 
            LIMIT %s
            """,
            (user_query_embedding, top_k)
        )
        results = cur.fetchall()
    return results

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