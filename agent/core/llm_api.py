# FILE: agent/core/llm_api.py
import openai
import requests # Aggiungi questo import


def call_llm(model_name: str, prompt: str, is_json_output: bool = False):
    """
    Funzione unificata per chiamare sia i modelli OpenAI che Gemini.
    """
    try:
        # Se è un modello Gemini, chiama il nostro microservizio
        if model_name.startswith("gemini"):
            gateway_url = "http://llm_gateway:3001/generate"
            payload = {
                "model_name": model_name,
                "prompt": prompt,
                "is_json_output": is_json_output
            }
            response = requests.post(gateway_url, json=payload)
            response.raise_for_status() # Lancia un errore per status 4xx/5xx
            return response.text # Il gateway restituisce testo puro

        # Altrimenti, usa OpenAI come prima
        else:
            messages = [{"role": "user", "content": prompt}]
            response = openai.chat.completions.create(
                model=model_name,
                messages=messages,
                response_format={"type": "json_object"} if is_json_output else None
            )
            return response.choices[0].message.content

    except Exception as e:
        print(f"❌ Errore durante la chiamata al modello {model_name}: {e}")
        return '{"error": "Chiamata al modello fallita"}'