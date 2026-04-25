"""
Servicio de Inteligencia Artificial (OpenAI)
Este archivo gestiona la comunicación con ChatGPT para dos tareas clave:
1. Resumir descripciones de productos para que sean atractivas.
2. Elegir automáticamente la categoría adecuada de un producto.
"""

import json
import logging
import requests
from src.config.settings import Config

logger = logging.getLogger(__name__)

class GPTService:
    """
    Se comunica con OpenAI mediante peticiones HTTP simples.
    Esto evita tener que instalar librerías adicionales y facilita el despliegue.
    """
    
    def __init__(self):
        self.api_key = Config.OPENAI_API_KEY
        self.url = "https://api.openai.com/v1/chat/completions"

    def sintetizar_descripcion(self, features: list[str]) -> str:
        """
        Pide a la IA que redacte un resumen persuasivo de 2 o 3 líneas 
        basándose en las características técnicas del producto.
        """
        if not features:
            return "Sin descripción técnica adicional."
            
        if not self.api_key:
            logger.warning("No se encontró OPENAI_API_KEY. Usando fallback.")
            return features[0]
            
        full_text = "\n- ".join(features)
        
        # El 'prompt' es la instrucción que le damos a la IA
        prompt = (
            "Eres un experto copywriter para un canal de chollos en Telegram.\n"
            "Sintetiza estas características en un bloque de texto MUY breve y persuasivo.\n"
            "Máximo 2 o 3 líneas. No uses muletillas. Empieza directo al grano.\n\n"
            "Características:\n- " + full_text
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4o-mini", # Modelo económico y muy rápido
            "messages": [
                {"role": "system", "content": "Eres un redactor de chollos. Escribes corto y directo."},
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
            logger.error(f"Error con OpenAI: {e}")
            return features[0]

    def seleccionar_categorias(self, titulo: str, descripcion_resumida: str, categorias_disponibles: list[str]) -> list[str]:
        """
        Analiza el producto y elige la mejor categoría (hashtag) de entre una lista permitida.
        """
        if not categorias_disponibles or not self.api_key:
            return []

        categorias_str = " ".join(categorias_disponibles)
        prompt = (
            "Elige 1 o 2 hashtags de esta lista que mejor describan el producto.\n"
            "Solo puedes usar hashtags de la lista. Responde solo con los hashtags.\n\n"
            f"Lista: {categorias_str}\n"
            f"Producto: {titulo}\n{descripcion_resumida}"
        )

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "Solo puedes usar las categorías proporcionadas."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2, # Baja temperatura para que sea más determinista
        }

        try:
            response = requests.post(self.url, headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }, json=payload, timeout=20)
            response.raise_for_status()
            raw = response.json()["choices"][0]["message"]["content"].strip()

            tokens = raw.replace(",", " ").split()
            permitidas = set(categorias_disponibles)
            return [t for t in tokens if t in permitidas][:2]
        except Exception:
            return []
