import grpc
import agent.tools.user_service_pb2 as user_service_pb2
import agent.tools.user_service_pb2_grpc as user_service_pb2_grpc
import requests
import json

from agent.core.field_extractor import FieldExtractor

def execute_tool(tool_call, context=None):
    metadata = tool_call.get("tool_metadata", {})
    api_type = metadata.get("type")

    if not api_type:
        return {"success": False, "error": f"Tipo di API mancante nei metadati: {metadata}"}

    print(f"⚙️ Esecuzione dello strumento di tipo '{api_type}'...")
    if api_type == "grpc": 
        result = execute_grpc_call(tool_call)
    elif api_type == "graphql": 
        result = execute_graphql_call(tool_call)
    elif api_type == "rest": 
        result = execute_rest_call(tool_call)
    else: 
        return {"success": False, "error": f"Tipo di API sconosciuto: {api_type}"}
    
    # NUOVA PARTE: Applica field extraction se richiesta
    if result.get("success") and tool_call.get("extract_fields"):
        original_data = result["data"]
        try:
            filtered_data = FieldExtractor.extract(original_data, tool_call["extract_fields"])
            
            # Log per debug
            original_size = len(json.dumps(original_data))
            filtered_size = len(json.dumps(filtered_data))
            print(f"   📉 Dati filtrati: {original_size} → {filtered_size} bytes ({filtered_size/original_size*100:.1f}%)")
            
            result["data"] = filtered_data
        except Exception as e:
            print(f"   ⚠️ Errore nell'estrazione campi: {e}. Uso dati completi.")
            # In caso di errore, mantieni i dati originali
    elif result.get("success"):
        result["data"] = FieldExtractor.smart_extract(
        result["data"], 
        context.get("current_task"),
        context.get("user_query"),
        context.get("full_plan"),
        "gemini-2.5-flash"
    )
    
    return result

def execute_grpc_call(tool_call):
    """Esegue una chiamata a un server gRPC."""
    metadata = tool_call.get("tool_metadata", {})
    payload = tool_call.get("payload", {})
    service_name = metadata.get("service")
    rpc_name = metadata.get("rpc")

    # Collega al server gRPC (che è in Docker sulla porta 50051)
    channel = grpc.insecure_channel('grpc_server:50051')
    
    try:
        if service_name == "UserService" and rpc_name == "GetUser":
            stub = user_service_pb2_grpc.UserServiceStub(channel)

            user_id = payload.get("id") or payload.get("userId") or payload.get("user_id")
            if user_id is None:
                return {"success": False, "error": "ID utente non trovato nel payload"}
            # Prepara la richiesta gRPC usando i dati dal payload
            request = user_service_pb2.GetUserRequest(id=int(user_id))
            # Esegui la chiamata
            response = stub.GetUser(request)
            return {"success": True, "data": {
                "id": response.id,
                "name": response.name,
                "email": response.email,
                "is_active": response.is_active
            }}
        else:
            return {"success": False, "error": f"Chiamata gRPC non implementata: {service_name}.{rpc_name}"}
    except grpc.RpcError as e:
        return {"success": False, "error": f"Errore gRPC: {e.details()}"}
    except Exception as e:
        return {"success": False, "error": f"Errore imprevisto: {str(e)}"}


def execute_graphql_call(tool_call):
    """
    Esegue una chiamata GraphQL generica.
    Si aspetta che il payload contenga 'query' e 'variables'.
    """
    payload = tool_call.get("payload", {})
    
    # L'LLM deve fornirci la query completa e le variabili
    query_string = payload.get("query")
    variables = payload.get("variables", {})

    if not query_string:
        return {"success": False, "error": "Payload per GraphQL non conteneva una 'query'."}

    # L'URL del nostro server GraphQL in Docker
    url = "http://graphql_server:8000/graphql"
    print(f"  -> Esecuzione GraphQL su {url}")
    print(f"     Query: {query_string.strip()}")
    print(f"     Variables: {variables}")

    try:
        json_payload = {"query": query_string, "variables": variables}
        response = requests.post(url, json=json_payload)
        response.raise_for_status()

        response_data = response.json()
        if "errors" in response_data:
            return {"success": False, "error": f"Errore GraphQL: {response_data['errors']}"}
        else:
            return {"success": True, "data": response_data.get("data")}

    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Errore di connessione HTTP: {e}"}
    except Exception as e:
        return {"success": False, "error": f"Errore imprevisto: {str(e)}"}

def execute_rest_call(tool_call):
    """
    Esegue una chiamata a un'API REST, gestendo correttamente 
    i parametri nel path, nella query string e nel body.
    """
    metadata = tool_call.get("tool_metadata", {})
    payload = tool_call.get("payload", {})
    
    base_url = metadata.get("base_url")
    path_template = metadata.get("path_template")
    method = metadata.get("method", "GET").upper()

    path_params = {}
    query_params = {}
    body_payload = {}

    # Separiamo i parametri in base alla loro destinazione
    for key, value in payload.items():
        if f"{{{key}}}" in path_template:
            path_params[key] = value
        # Per i metodi che hanno un body, tutto il resto va nel body.
        elif method in ["POST", "PUT", "PATCH"]:
            body_payload[key] = value
        # Altrimenti (per GET, DELETE etc.), va nella query.
        else:
            query_params[key] = value
            
    try:
        final_path = path_template.format(**path_params)
    except KeyError as e:
        # Log dettagliato per debug
        print(f"  ❌ Path template: {path_template}")
        print(f"  ❌ Path params disponibili: {path_params}")
        print(f"  ❌ Payload completo ricevuto: {payload}")
        return {"success": False, "error": f"Parametro mancante nel payload per il path: {e}"}

    url = f"{base_url}{final_path}"
    print(f"  -> Esecuzione {method} su URL: {url}")
    if query_params:
        print(f"     Query Params: {query_params}")
    if body_payload:
        print(f"     Body: {body_payload}")

    try:
        response = requests.request(
            method, 
            url, 
            params=query_params or None,
            json=body_payload or None
        )
        response.raise_for_status()
        
        if response.status_code == 204:
            return {"success": True, "data": "Operazione completata con successo (No Content)."}
        
        return {"success": True, "data": response.json()}
    except requests.exceptions.HTTPError as e:
        return {"success": False, "error": f"Errore HTTP: {e.response.status_code}", "data": e.response.text}
    except Exception as e:
        return {"success": False, "error": f"Errore imprevisto durante la chiamata REST: {str(e)}"}