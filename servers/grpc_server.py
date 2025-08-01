from concurrent import futures
import grpc
import time

# Importa le classi generate
import user_service_pb2
import user_service_pb2_grpc

# Dati finti per il nostro server
FAKE_USERS = {
    1: {"id": 1, "name": "Mario Rossi", "email": "mario.rossi@example.com", "is_active": True},
    2: {"id": 2, "name": "Laura Bianchi", "email": "laura.bianchi@example.com", "is_active": False},
}

# Questa è l'implementazione del nostro servizio
class UserServiceServicer(user_service_pb2_grpc.UserServiceServicer):
    def GetUser(self, request, context):
        print(f"Richiesta gRPC ricevuta per l'utente ID: {request.id}")
        user_data = FAKE_USERS.get(request.id)

        if user_data:
            return user_service_pb2.UserResponse(**user_data)
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Utente con ID {request.id} non trovato.")
            return user_service_pb2.UserResponse()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_service_pb2_grpc.add_UserServiceServicer_to_server(UserServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("Avvio del server gRPC sulla porta 50051...")
    server.start()
    try:
        while True:
            time.sleep(86400) # Dormi per un giorno
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()
