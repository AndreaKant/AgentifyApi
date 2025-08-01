# File: servers/rest.Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
COPY reviews_server.py .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8003
CMD ["uvicorn", "reviews_server:app", "--host", "0.0.0.0", "--port", "8003"]