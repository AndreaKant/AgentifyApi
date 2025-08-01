FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
COPY graphql_server.py .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "graphql_server:app", "--host", "0.0.0.0", "--port", "8000"]