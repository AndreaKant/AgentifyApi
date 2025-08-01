import json
from typing import Any, List, Dict, Union

class FieldExtractor:
    """Estrae campi specifici da risposte JSON complesse."""
    
    @staticmethod
    def extract(data: Union[Dict, List], field_paths: List[str]) -> Union[Dict, List]:
        """
        Estrae solo i campi specificati dal JSON.
        
        Supporta:
        - Campi semplici: "name"
        - Campi nested: "user.email"
        - Array: "items[].name"
        - Array con indice: "items[0].name"
        """
        if not field_paths:
            return data
            
        if isinstance(data, list):
            # Se data è una lista, applica l'estrazione a ogni elemento
            return [FieldExtractor._extract_from_dict(item, field_paths) 
                    for item in data if isinstance(item, dict)]
        
        return FieldExtractor._extract_from_dict(data, field_paths)
    
    @staticmethod
    def _extract_from_dict(data: Dict, field_paths: List[str]) -> Dict:
        result = {}
        
        for path in field_paths:
            try:
                value = FieldExtractor._get_nested_value(data, path)
                if value is not None:
                    # Ricostruisci la struttura
                    FieldExtractor._set_nested_value(result, path, value)
            except:
                # Se il path non esiste, skip
                continue
                
        return result
    
    @staticmethod
    def _get_nested_value(data: Dict, path: str) -> Any:
        """Naviga nel JSON seguendo il path."""
        parts = path.replace('[].', '[*].').split('.')
        current = data
        
        for part in parts:
            if '[' in part:
                # Gestione array
                field_name = part.split('[')[0]
                if field_name:
                    current = current.get(field_name, [])
                
                if '[*]' in part:
                    # Estrai da tutti gli elementi
                    remaining_path = '.'.join(parts[parts.index(part)+1:])
                    if remaining_path:
                        return [FieldExtractor._get_nested_value(item, remaining_path) 
                                for item in current if isinstance(item, dict)]
                    return current
                elif '[' in part and ']' in part:
                    # Indice specifico
                    idx = int(part.split('[')[1].split(']')[0])
                    current = current[idx] if idx < len(current) else None
            else:
                current = current.get(part) if isinstance(current, dict) else None
                
            if current is None:
                return None
                
        return current
    
    @staticmethod
    def _set_nested_value(result: Dict, path: str, value: Any):
        """Imposta il valore nel result mantenendo la struttura."""
        # Semplificazione: mette tutto al top level con chiave descrittiva
        clean_path = path.replace('[].', '_').replace('.', '_')
        result[clean_path] = value

    # Aggiungi una versione più smart che usa LLM
    def smart_extract(data: Union[Dict, List], current_task: str, user_query: str = None, full_plan: list = None, llm_model: str = "gemini-2.5-flash") -> Union[Dict, List]:
        """Usa un LLM per decidere quali campi estrarre basandosi sul task."""
        from ..core.llm_api import call_llm
        
        data_sample = json.dumps(data, indent=2)
        if len(data_sample) > 1500:
            data_sample = data_sample[:1500] + "\n... (truncated)"
        
        prompt = f"""
        Query originale dell'utente: "{user_query or 'Non disponibile'}"
        Task corrente: "{current_task}"
        Piano completo: {json.dumps(full_plan) if full_plan else 'Non disponibile'}
        
        Risposta API ricevuta:
        {data_sample}
        
        Identifica SOLO i campi necessari per questo task specifico nel contesto del piano generale.
        Rispondi con un JSON array di field paths.
        
        Esempi:
        - Per "quanto pesa X?": ["weight", "name"]
        - Per "qual è il prezzo del prodotto più costoso?": ["price", "name", "id"]
        - Per "trova email utente": ["email", "name"]
        
        Sii MINIMALISTA: estrai solo i campi strettamente necessari per questo step.
        """
            
        paths_str = call_llm(llm_model, prompt, is_json_output=True)
        try:
            paths = json.loads(paths_str)
            return FieldExtractor.extract(data, paths)
        except:
            print("   ⚠️ Smart extract fallito, ritorno dati completi")
            return data