"""
Servicio de Publicación
Este archivo es el responsable de enviar los mensajes finales a las redes sociales 
(actualmente Telegram). Se encarga de elegir el canal correcto (Admin o Principal), 
aplicar el formato visual premium y realizar el envío físico del mensaje.
"""

import logging
from src.integrations.telegram.telegram_api import TelegramBotAPI
from src.config.settings import Config

logger = logging.getLogger(__name__)

class PublisherService:
    """
    Gestiona el envío de chollos a los diferentes canales de Telegram.
    Sabe qué tokens y qué IDs de canal usar según la configuración.
    """
    
    def __init__(self):
        # Cargamos las claves de acceso desde la configuración central
        self.default_bot_token = Config.TELEGRAM_BOT_TOKEN
        self.default_admin_channel_id = Config.TELEGRAM_ADMIN_CHANNEL_ID
        self.default_main_channel_id = Config.TELEGRAM_MAIN_CHANNEL_ID

    def publish_to_admin(self, text: str, photo_url: str = None) -> bool:
        """Envía un chollo al canal de pruebas (Admin)."""
        return self.publish_to_telegram(text, photo_url, channel_id=self.default_admin_channel_id)
        
    def publish_to_main(self, text: str, photo_url: str = None) -> bool:
        """Envía un chollo al canal principal (Público)."""
        return self.publish_to_telegram(text, photo_url, channel_id=self.default_main_channel_id)

    def publish_to_telegram(self, text: str, photo_url: str = None, bot_token: str = None, channel_id: str = None) -> bool:
        """
        Lógica central de envío. Aplica los emojis premium justo antes de 
        mandar el mensaje a la API de Telegram.
        """
        token = bot_token or self.default_bot_token
        
        if not token or not channel_id:
            logger.error("Faltan credenciales de Telegram.")
            raise ValueError("Configura TELEGRAM_BOT_TOKEN y el ID del canal en el archivo .env")
            
        tg_api = TelegramBotAPI(token)
        
        from src.formatters.telegram_formatter import format_text_with_custom_emojis
        
        # Convertimos los emojis normales en 'Custom Emojis' de Telegram Premium
        payload = format_text_with_custom_emojis(text)
        
        if photo_url:
            # Si hay imagen, la enviamos con el texto como pie de foto
            tg_api.send_photo(
                chat_id=channel_id, 
                photo_url=photo_url, 
                caption=payload["text"], 
                entities=payload["entities"]
            )
        else:
            # Si no hay imagen, enviamos solo el texto
            tg_api.send_message(
                chat_id=channel_id, 
                text=payload["text"], 
                parse_mode=None,
                entities=payload["entities"]
            )
        
        return True
