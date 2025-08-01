# Usa un'immagine Python ufficiale come base
FROM python:3.11-slim

# Imposta la directory di lavoro nel container
WORKDIR /app

# Copia i file necessari nella directory di lavoro
COPY requirements.txt .
COPY user_service_pb2.py .
COPY user_service_pb2_grpc.py .
COPY grpc_server.py .

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Esponi la porta su cui il server gRPC ascolterà
EXPOSE 50051

# Il comando per avviare il server quando il container parte
CMD ["python", "grpc_server.py"]