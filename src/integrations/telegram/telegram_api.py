"""
Cliente API de Telegram (Bot)
Este archivo gestiona el envío de mensajes y fotos a Telegram usando un Bot. 
Está diseñado para ser ligero y no depender de grandes librerías, realizando 
peticiones web directas a los servidores de Telegram.
"""

import logging
import requests

logger = logging.getLogger(__name__)

class TelegramBotAPI:
    """
    Se encarga de publicar en canales de Telegram.
    Usa el token del bot y el ID del canal configurados en el sistema.
    """
    
    BASE_URL = "https://api.telegram.org/bot{token}"

    def __init__(self, token: str):
        self.token = token
        self.api_url = self.BASE_URL.format(token=self.token)

    def send_photo(self, chat_id: str, photo_url: str, caption: str = "", entities: list = None) -> dict:
        """Envía una imagen con un texto descriptivo debajo."""
        if not self.token or not chat_id:
            raise ValueError("Configuración de Telegram incompleta.")
            
        url = f"{self.api_url}/sendPhoto"
        payload = {
            "chat_id": chat_id,
            "photo": photo_url,
            "caption": caption
        }
        
        # Las 'entities' permiten aplicar formatos como negrita o emojis premium
        if entities:
            payload["caption_entities"] = entities
            
        try:
            response = requests.post(url, json=payload, timeout=25)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error enviando foto: {e}")
            raise RuntimeError(f"Falla de conexión con Telegram.")

    def send_message(self, chat_id: str, text: str, parse_mode: str = "HTML", entities: list = None) -> dict:
        """Envía un mensaje de texto simple o con formato avanzado."""
        if not self.token or not chat_id:
            raise ValueError("Configuración de Telegram incompleta.")
            
        url = f"{self.api_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": False # Permite que aparezca la ficha del producto
        }
        
        if entities:
            payload["entities"] = entities
        elif parse_mode:
            payload["parse_mode"] = parse_mode
            
        try:
            response = requests.post(url, json=payload, timeout=20)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error enviando mensaje: {e}")
            raise RuntimeError(f"Falla de conexión con Telegram.")
