import os
from typing import Optional

def load_config():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

# Ejecutamos al importar
load_config()

class Config:
    # Amazon API Config
    AMAZON_CLIENT_ID: str = os.getenv("AMAZON_CLIENT_ID", "")
    AMAZON_CLIENT_SECRET: str = os.getenv("AMAZON_CLIENT_SECRET", "")
    AMAZON_AFFILIATE_TAG: str = os.getenv("AMAZON_AFFILIATE_TAG", "buenchollo0b-21")
    
    # Telegram Config
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_ADMIN_CHANNEL_ID: str = os.getenv("TELEGRAM_ADMIN_CHANNEL_ID", os.getenv("TELEGRAM_CHANNEL_ID", ""))
    TELEGRAM_MAIN_CHANNEL_ID: str = os.getenv("TELEGRAM_MAIN_CHANNEL_ID", "")
    
    # OpenAI Config para copys atractivos
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
