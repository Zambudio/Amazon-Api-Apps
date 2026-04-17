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

    def seleccionar_categorias(self, titulo: str, descripcion_resumida: str, categorias_disponibles: list[str]) -> list[str]:
        """
        Dado un título y una breve descripción del producto, pide a GPT que escoja
        1 o 2 categorías de entre las ya existentes en el JSON.
        Si con una categoría basta, debe preferir regresar solo una.
        Nunca debe inventar categorías nuevas y el código filtrará cualquier
        categoría que no esté en la lista proporcionada.
        """
        if not categorias_disponibles:
            return []

        if not self.api_key:
            logger.warning("No se encontró OPENAI_API_KEY. No se seleccionarán categorías por IA.")
            return []

        categorias_str = " ".join(categorias_disponibles)
        prompt = (
            "Eres un asistente que clasifica productos tecnológicos en categorías existentes.\n"
            "Tienes una lista de hashtags de categorías que ya están definidas para un canal de chollos en Telegram.\n\n"
            "Tarea:\n"
            "- Lee el título y la descripción corta de un producto.\n"
            "- Elige 1 o 2 hashtags de la lista proporcionada que mejor describan el producto.\n"
            "- Si con un solo hashtag es suficiente, prefierelo y devuelve solo uno.\n"
            "- Usa exactamente los mismos hashtags de la lista (copiados tal cual), sin inventar ninguno nuevo.\n"
            "- Prioriza las categorías más específicas.\n\n"
            "Formato de respuesta:\n"
            "- Devuelve SOLO una línea con los hashtags separados por espacios, por ejemplo:\n"
            "  #Monitores #Gaming\n"
            "- Si un hashtag basta, responde con una sola etiqueta.\n\n"
            "Lista de categorías disponibles:\n"
            f"{categorias_str}\n\n"
            "Producto a clasificar:\n"
            f"Título: {titulo}\n"
            f"Descripción: {descripcion_resumida}\n"
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": "Eres un clasificador de productos. Solo puedes usar las categorías proporcionadas."
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }

        try:
            response = requests.post(self.url, headers=headers, json=payload, timeout=20)
            response.raise_for_status()
            data = response.json()
            raw = data["choices"][0]["message"]["content"].strip()

            # Extraemos hashtags de la respuesta y filtramos por los permitidos
            tokens = raw.replace(",", " ").split()
            candidatos = [t for t in tokens if t.startswith("#")]

            permitidas = set(categorias_disponibles)
            seleccionadas = [t for t in candidatos if t in permitidas]

            # Limitamos a máximo 2 hashtags, prefiriendo 1 si con uno basta
            return seleccionadas[:2]
        except Exception as e:
            logger.error(f"Error seleccionando categorías con OpenAI: {e}")
            return []
