import logging
from src.integrations.telegram.telegram_api import TelegramBotAPI
from src.config.settings import Config

logger = logging.getLogger(__name__)

class PublisherService:
    """
    Fachada para publicar contenido. 
    Actualmente configurado para enviar a Telegram, pero está estructurado 
    para admitir múltiples bots o redes (Twitter, Facebook) en el futuro según
    la configuración seleccionada.
    """
    
    def __init__(self):
        # Configuramos credenciales del bot por defecto
        self.default_bot_token = Config.TELEGRAM_BOT_TOKEN
        self.default_admin_channel_id = Config.TELEGRAM_ADMIN_CHANNEL_ID
        self.default_main_channel_id = Config.TELEGRAM_MAIN_CHANNEL_ID

    def publish_to_admin(self, text: str, photo_url: str = None) -> bool:
        return self.publish_to_telegram(text, photo_url, channel_id=self.default_admin_channel_id)
        
    def publish_to_main(self, text: str, photo_url: str = None) -> bool:
        return self.publish_to_telegram(text, photo_url, channel_id=self.default_main_channel_id)

    def publish_to_telegram(self, text: str, photo_url: str = None, bot_token: str = None, channel_id: str = None) -> bool:
        """
        Envía definitivamente el texto renderizado a Telegram.
        """
        token = bot_token or self.default_bot_token
        
        if not token or not channel_id:
            logger.error("No se puede publicar: Falta TELEGRAM_BOT_TOKEN o ID_DEL_CANAL")
            raise ValueError("Faltan credenciales o no se ha configurado el ID del canal de destino en el .env")
            
        tg_api = TelegramBotAPI(token)
        
        from src.formatters.telegram_formatter import format_text_with_custom_emojis
        
        # Mapeamos text plano a text + entities de Custom Emojis (Premium)
        # Esto ocurre justo antes de enviar, permitiendo que el usuario lo haya editado todo como texto plano en el UI.
        payload = format_text_with_custom_emojis(text)
        
        if photo_url:
            # Publicación de FOTO con caption (el texto es el pie de foto)
            tg_api.send_photo(
                chat_id=channel_id, 
                photo_url=photo_url, 
                caption=payload["text"], 
                entities=payload["entities"]
            )
        else:
            # Publicación de SOLO TEXTO
            tg_api.send_message(
                chat_id=channel_id, 
                text=payload["text"], 
                parse_mode=None,
                entities=payload["entities"]
            )
        
        return True
