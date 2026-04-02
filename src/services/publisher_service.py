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
        self.default_channel_id = Config.TELEGRAM_CHANNEL_ID
        
        # Arquitectura preparada para el futuro multi-bot:
        # self.registered_bots = {
        #     "principal": TelegramBotAPI(token_1),
        #     "canal_secundario": TelegramBotAPI(token_2)
        # }

    def publish_to_telegram(self, text: str, photo_url: str = None, bot_token: str = None, channel_id: str = None) -> bool:
        """
        Envía definitivamente el texto renderizado a Telegram.
        Si hay photo_url, lo envía como Foto con el texto de pie de página (caption).
        Si no, envía solo el texto.
        """
        token = bot_token or self.default_bot_token
        channel = channel_id or self.default_channel_id
        
        if not token or not channel:
            logger.error("No se puede publicar: Falta TELEGRAM_BOT_TOKEN o TELEGRAM_CHANNEL_ID")
            raise ValueError("Faltan credenciales de Telegram. Asegúrate de tener TELEGRAM_BOT_TOKEN y TELEGRAM_CHANNEL_ID en el archivo .env")
            
        tg_api = TelegramBotAPI(token)
        
        from src.formatters.telegram_formatter import format_text_with_custom_emojis
        
        # Mapeamos text plano a text + entities de Custom Emojis (Premium)
        # Esto ocurre justo antes de enviar, permitiendo que el usuario lo haya editado todo como texto plano en el UI.
        payload = format_text_with_custom_emojis(text)
        
        if photo_url:
            # Publicación de FOTO con caption (el texto es el pie de foto)
            tg_api.send_photo(
                chat_id=channel, 
                photo_url=photo_url, 
                caption=payload["text"], 
                entities=payload["entities"]
            )
        else:
            # Publicación de SOLO TEXTO
            tg_api.send_message(
                chat_id=channel, 
                text=payload["text"], 
                parse_mode=None,
                entities=payload["entities"]
            )
        
        return True
