import os
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"

"""TODO: Redis"""
embedding_cache = {}

def get_embedding(text, model=EMBEDDING_MODEL):
   """Funzione helper per chiamare l'API di embedding di OpenAI."""
   cache_key = (text, model)
   if cache_key in embedding_cache:
       return embedding_cache[cache_key]
   text = text.replace("\n", " ")
   response = openai.embeddings.create(input=[text], model=model)
   embedding = response.data[0].embedding
   embedding_cache[cache_key] = embedding
   return embedding