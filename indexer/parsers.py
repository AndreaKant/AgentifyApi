import json
import requests
import os

# --- Import delle nuove librerie robuste ---
from graphql import parse, visit, Visitor, print_ast
from prance import ResolvingParser

GRPC_PARSER_URL = os.getenv("GRPC_PARSER_URL", "http://grpc_parser:3000")

def parse_grpc_contracts_via_service(proto_file_path):
    """
    NUOVO: Chiama il microservizio Node.js per parsare i file .proto.
    """
    print(f"📡 Invio {proto_file_path} al servizio di parsing gRPC...")
    try:
        with open(proto_file_path, 'r') as f:
            proto_content = f.read()
        
        response = requests.post(
            f"{GRPC_PARSER_URL}/parse",
            data=proto_content,
            headers={'Content-Type': 'text/plain'}
        )
        response.raise_for_status() # Lancia un errore per status code 4xx/5xx
        
        parsed_functions = response.json()
        print(f"  -> ✅ Ricevute {len(parsed_functions)} funzioni gRPC.")
        return parsed_functions

    except requests.exceptions.RequestException as e:
        print(f"❌ Impossibile contattare il servizio di parsing gRPC: {e}")
        return []
    except Exception as e:
        print(f"❌ Errore imprevisto durante il parsing gRPC: {e}")
        return []

def parse_graphql_schema(schema_file_path):
    """
    RIFATTO: Usa graphql-core per parsare lo schema GraphQL in modo robusto.
    """
    print(f"📚 Parsing dello schema GraphQL da {schema_file_path}...")
    functions = []
    try:
        with open(schema_file_path, 'r') as f:
            schema_string = f.read()

        ast = parse(schema_string) # Crea l'Abstract Syntax Tree

        # CORREZIONE: La classe deve ereditare da graphql.Visitor
        class GraphQLVisitor(Visitor):
            def enter_object_type_definition(self, node, key, parent, path, ancestors):
                node_name = node.name.value
                if node_name not in ["Query", "Mutation"]:
                    return

                for field in node.fields:
                    operation_name = field.name.value
                    description = (field.description.value if field.description else "").strip()
                    
                    # Usiamo print_ast per ottenere una rappresentazione testuale pulita del contratto
                    source_contract = print_ast(field)

                    functions.append({
                        "type": "graphql",
                        "name": operation_name,
                        "description": description,
                        "metadata": {
                            "name": operation_name,
                            "type": "graphql",
                            "operation_type": node_name,
                            "operation_name": operation_name
                        },
                        "source_contract": source_contract
                    })
        
        visit(ast, GraphQLVisitor())
        print(f"  -> ✅ Trovate {len(functions)} operazioni GraphQL.")
        return functions
    except FileNotFoundError:
        print(f"❌ File non trovato: {schema_file_path}")
        return []
    except Exception as e:
        print(f"❌ Errore durante il parsing di GraphQL: {e}")
        return []


def parse_openapi_schema(schema_url):
    """
    RIFATTO: Ora capisce il base_url dinamicamente.
    """
    print(f"   Download e parsing da {schema_url}...")
    functions = []
    try:
        parser = ResolvingParser(schema_url, strict=False)
        schema = parser.specification
    except Exception as e:
        print(f"   ❌ Impossibile scaricare o parsare lo schema: {e}")
        return []

    # --- LOGICA DINAMICA PER IL BASE URL ---
    # Estrae lo schema (http/https), l'host (es. 'rest_server') e la porta (es. 8001) dall'URL
    from urllib.parse import urlparse
    parsed_url = urlparse(schema_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    print(f"   -> Base URL rilevato: {base_url}")
    
    for path, methods in schema.get('paths', {}).items():
        for method, details in methods.items():
            if not isinstance(details, dict): continue

            description = details.get('description') or details.get('summary', '')
            function_name = details.get('operationId') or details.get('summary', f"{method.upper()} {path}")
            functions.append({
                "type": "rest",
                "name": details.get('operationId') or details.get('summary', f"{method.upper()} {path}"),
                "description": description,
                "metadata": {
                    "name": function_name, 
                    "type": "rest",
                    "base_url": base_url, # <-- Usa il base_url dinamico
                    "path_template": path,
                    "method": method.upper()
                },
                "source_contract": json.dumps({path: {method: details}}, indent=2) 
            })
            
    print(f"   -> ✅ Trovati {len(functions)} endpoint.")
    return functions
