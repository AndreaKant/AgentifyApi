import json

EMBEDDING_DIMENSIONS = 1536

def create_table_if_not_exists(conn):
    """Crea la tabella per le funzioni API se non esiste già."""
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS api_functions (
                id SERIAL PRIMARY KEY,
                embedding VECTOR({EMBEDDING_DIMENSIONS}),
                metadata JSONB,
                source_contract TEXT
            );
        """)
        print("Tabella 'api_functions' pronta.")
    conn.commit()

def insert_api_functions(conn, all_api_functions, get_embedding_func):
    """Calcola gli embedding e inserisce le funzioni nel database."""
    with conn.cursor() as cur:
        print("Inizio calcolo embeddings e inserimento nel database...")
        for func in all_api_functions:
            text_to_embed = f"Tipo: {func['type']}, Nome: {func['name']}, Descrizione: {func['description']}"
            embedding = get_embedding_func(text_to_embed) # Usa la funzione passata come argomento
            print(f"  -> Calcolato embedding per '{func['name']}'")
            cur.execute(
                "INSERT INTO api_functions (embedding, metadata, source_contract) VALUES (%s, %s, %s)",
                (embedding, json.dumps(func.get('metadata', {})), func.get('source_contract', ''))
            )
        print(f"Inserite {len(all_api_functions)} funzioni nel database.")
    conn.commit()