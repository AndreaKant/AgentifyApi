import os
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"

def get_embedding(text, model=EMBEDDING_MODEL):
   """Funzione helper per chiamare l'API di embedding di OpenAI."""
   text = text.replace("\n", " ")
   response = openai.embeddings.create(input=[text], model=model)
   return response.data[0].embedding