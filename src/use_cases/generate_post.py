from typing import Optional
from src.services.amazon_service import AmazonService
from src.integrations.openai.gpt_service import GPTService
from src.formatters.telegram_formatter import format_telegram_message

class GeneratePostUseCase:
    """
    Caso de uso: Coge un input (URL o ASIN), extrae la información 
    y genera el formato listo para Telegram.
    """
    
    def __init__(self, amazon_service=AmazonService(), gpt_service=GPTService()):
        self.amazon_service = amazon_service
        self.gpt_service = gpt_service
        
    def execute(self, url_or_asin: str) -> dict:
        """
        Ejecuta el flujo principal y retorna el mensaje formateado 
        y el objeto de producto completo.
        """
        # 1. Extracción de datos (Amazon)
        product_info = self.amazon_service.get_product(url_or_asin)
        
        if not product_info:
            return {"text": None, "product": None}
            
        # Preservar URL de entrada
        url_or_asin_limpio = url_or_asin.strip()
        if url_or_asin_limpio.startswith("http"):
            product_info.url_afiliado = url_or_asin_limpio
            
        # 2. Sintetizar la descripción larga en un copy atractivo usando ChatGPT
        if product_info.descripcion:
            product_info.descripcion_gpt = self.gpt_service.sintetizar_descripcion(product_info.descripcion)
            
        # 3. Generación del mensaje / publicación
        mensaje = format_telegram_message(product_info)
        
        return {"text": mensaje, "product": product_info}
