import os
import json
import time
from dotenv import load_dotenv

from indexer.parsers import parse_grpc_contracts_via_service, parse_graphql_schema, parse_openapi_schema
from indexer.db_utils import create_table_if_not_exists, insert_api_functions
from utils.database import get_db_connection
from utils.embeddings import get_embedding

# Carica le variabili d'ambiente dal file .env
load_dotenv()

def main():
    """Orchestra il processo di indicizzazione delle API."""
    conn = get_db_connection()
    if not conn:
        return

    # 1. Prepara il Database
    create_table_if_not_exists(conn)
    with conn.cursor() as cur:
        cur.execute("TRUNCATE api_functions RESTART IDENTITY;")
        print("Tabella pulita.")
    conn.commit()

    # 2. Raccogli le Definizioni delle API da tutte le fonti
    all_api_functions = []
    print("--- Inizio Parsing delle API ---")

     # Pausa per dare tempo ai servizi Docker di avviarsi
    print("⏳ In attesa del servizio di parsing gRPC...")
    time.sleep(5)
    all_api_functions.extend(parse_grpc_contracts_via_service('contracts/user_service.proto'))
    all_api_functions.extend(parse_graphql_schema('contracts/schema.graphql'))

    print("⏳ In attesa dei server REST...")
    time.sleep(3)
    rest_api_targets = [
        {"name": "Orders", "url": "http://rest_server:8001/openapi.json"},
        {"name": "Geolocation", "url": "http://geo_server:8002/openapi.json"},
        {"name": "Reviews", "url": "http://reviews_server:8003/openapi.json"},
    ]
    
    for api in rest_api_targets:
        print(f"--- Scansione API REST: {api['name']} ---")
        all_api_functions.extend(parse_openapi_schema(api["url"]))

    print("--- Aggiunta API Pokemon per testing ---")
    pokemon_apis = [
        {
            "type": "rest",
            "name": "get_pokemon_details",
            "description": "Ottieni dettagli completi di un Pokemon inclusi tipo, abilità, statistiche, peso e altezza. Usa il nome (es: 'pikachu') o l'ID numerico.",
            "metadata": {
                "name": "get_pokemon_details",
                "type": "rest",
                "base_url": "https://pokeapi.co",
                "path_template": "/api/v2/pokemon/{name_or_id}",
                "method": "GET"
            },
            "source_contract": "GET /api/v2/pokemon/{name_or_id} - Returns: name, types[], abilities[], stats[], weight, height"
        }
    ]
    all_api_functions.extend(pokemon_apis)
    
     # 3. Indicizza le funzioni nel Database
    if not all_api_functions:
        print("❌ Nessuna funzione da indicizzare. Termino.")
        conn.close()
        return

    print(f"\n✅ Trovate in totale {len(all_api_functions)} funzioni API da indicizzare.")
    insert_api_functions(conn, all_api_functions, get_embedding) # Passiamo la funzione get_embedding

    conn.close()
    print("\n🎉 Indicizzazione completata con successo!")


if __name__ == '__main__':
    main()