import os
import psycopg2
from pgvector.psycopg2 import register_vector

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

def get_db_connection():
    """Stabilisce la connessione al database PostgreSQL."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
        )
        register_vector(conn)
        print("Connessione al database riuscita.")
        return conn
    except psycopg2.OperationalError as e:
        print(f"Errore di connessione al database: {e}")
        return None