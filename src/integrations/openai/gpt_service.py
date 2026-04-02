import json
import logging
import requests
from src.config.settings import Config

logger = logging.getLogger(__name__)

class GPTService:
    """
    Servicio para conectar con la API de OpenAI (ChatGPT) sin requerir instalar 
    el paquete oficial de 'openai', para máxima compatibilidad usando 'requests'.
    """
    
    def __init__(self):
        self.api_key = Config.OPENAI_API_KEY
        self.url = "https://api.openai.com/v1/chat/completions"

    def sintetizar_descripcion(self, features: list[str]) -> str:
        """
        Toma una lista de características crudas de un producto y le pide a GPT 
        que las sintetice en un pequeño bloque de texto atractivo.
        """
        if not features:
            return "Sin descripción técnica adicional."
            
        if not self.api_key:
            # Fallback seguro si no hay API Key configurada
            logger.warning("No se encontró OPENAI_API_KEY. Usando primera línea como fallback.")
            return features[0]
            
        full_text = "\n- ".join(features)
        
        prompt = (
            "Eres un experto copywriter comercial para un canal de chollos tecnológicos en Telegram.\n"
            "Tu objetivo es leer las características técnicas de un producto y "
            "sintetizarlas en un único bloque de texto MUY breve, muy atractivo y persuasivo.\n\n"
            "Restricciones:\n"
            "- Máximo 2 o 3 líneas cortas.\n"
            "- Prohibido empezar con muletillas como 'Descubre...', 'Presentamos...', 'Eleva tu...', 'Transforma tu...', 'Experimenta el...'.\n"
            "- Empieza directamente hablando del producto o de su beneficio principal.\n"
            "- No uses viñetas (- o *), redáctalo como un pequeño párrafo fluido y directo.\n"
            "- No incluyas hashtags ni menciones al canal.\n"
            "- No inventes características que no estén en el texto original.\n\n"
            "Características originales:\n- " + full_text
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4o-mini", # Modelo más rápido y barato, perfecto para tareas cortas
            "messages": [
                {"role": "system", "content": "Eres un asistente de redacción para comercio electrónico. Escribes corto, directo y tentador."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.6
        }
        
        try:
            response = requests.post(self.url, headers=headers, json=payload, timeout=20)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Error procesando el copy con OpenAI: {e}")
            # Si falla GPT (ej. se cae la red o API Key mal configurada), usamos plan B seguro
            return features[0]
