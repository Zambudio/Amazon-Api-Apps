import logging
import requests

logger = logging.getLogger(__name__)

class TelegramBotAPI:
    """
    Cliente REST simple y puro para la API de Telegram.
    Enfocado en publicación de mensajes sin necesitar un framework pesado (como aiogram o python-telegram-bot)
    ya que aquí la aplicación actúa como emisor unidireccional por ahora.
    """
    
    BASE_URL = "https://api.telegram.org/bot{token}"

    def __init__(self, token: str):
        self.token = token
        self.api_url = self.BASE_URL.format(token=self.token)

    def send_photo(self, chat_id: str, photo_url: str, caption: str = "", entities: list = None) -> dict:
        """
        Envía una imagen con pie de foto (caption).
        """
        if not self.token or not chat_id:
            raise ValueError("Token de bot o Channel ID no configurados.")
            
        url = f"{self.api_url}/sendPhoto"
        payload = {
            "chat_id": chat_id,
            "photo": photo_url,
            "caption": caption
        }
        
        if entities:
            payload["caption_entities"] = entities
            
        try:
            response = requests.post(url, json=payload, timeout=25)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"Error HTTP enviando foto a Telegram: {e.response.text}")
            raise RuntimeError(f"Error enviando foto: {e.response.text}")
        except Exception as e:
            logger.error(f"Error grave conectando con Telegram: {e}")
            raise RuntimeError(f"Falla de conexión: {e}")

    def send_message(self, chat_id: str, text: str, parse_mode: str = "HTML", entities: list = None) -> dict:
        """
        Envía un texto a un chat o canal.
        """
        if not self.token or not chat_id:
            raise ValueError("Token de bot o Channel ID no configurados.")
            
        url = f"{self.api_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": False  # Fundamental para que se vea la preview de Amazon
        }
        
        # Si vienen entities, ignoramos parse_mode (chocan en la API pura)
        if entities:
            payload["entities"] = entities
        elif parse_mode:
            payload["parse_mode"] = parse_mode
            
        try:
            response = requests.post(url, json=payload, timeout=20)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"Error HTTP interactuando con Telegram: {e.response.text}")
            raise RuntimeError(f"Error desde Telegram: {e.response.text}")
        except Exception as e:
            logger.error(f"Error grave conectando con Telegram: {e}")
            raise RuntimeError(f"Falla de conexión: {e}")
