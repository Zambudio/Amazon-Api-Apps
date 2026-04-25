"""
Caso de Uso: Generar Post
Este archivo contiene la lógica principal para crear un post de Telegram. 
Orquesta a los diferentes servicios: pide datos a Amazon, solicita un resumen 
a la IA de OpenAI y usa el formateador para crear el mensaje final.
"""

from typing import Optional
from src.services.amazon_service import AmazonService
from src.integrations.openai.gpt_service import GPTService
from src.integrations.storage.json_category_repository import JsonCategoryRepository
from src.config.settings import Config
from src.domain.hashtag_rules import normalize_hashtag
from src.formatters.telegram_formatter import format_telegram_message

class GeneratePostUseCase:
    """
    Clase que ejecuta el proceso completo de creación de un mensaje de oferta.
    Es el nexo de unión entre la extracción de datos y la presentación final.
    """
    
    def __init__(self, amazon_service=AmazonService(), gpt_service=GPTService()):
        self.amazon_service = amazon_service
        self.gpt_service = gpt_service
        self.category_repository = JsonCategoryRepository(Config.CATEGORIES_FILE_PATH)
        
    def _fallback_select_categories(self, text: str, available: list[str]) -> list[str]:
        """Método de respaldo que busca palabras clave si la IA falla al elegir categorías."""
        text_lower = text.lower()
        selected: list[str] = []

        for category in available:
            normalized = normalize_hashtag(category)
            if not normalized: continue
            keyword = normalized.lstrip("#").lower()
            if keyword in text_lower and normalized not in selected:
                selected.append(normalized)
                if len(selected) >= 2: break
        return selected

    def execute(self, url_or_asin: str) -> dict:
        """
        Realiza la extracción, el resumen por IA y el formateo del post.
        Devuelve un diccionario con el texto final y el objeto del producto.
        """
        # 1. Obtenemos la información técnica de Amazon
        product_info = self.amazon_service.get_product(url_or_asin)
        if not product_info:
            return {"text": None, "product": None}
            
        # 2. Pedimos a la IA (GPT) que escriba un resumen persuasivo
        if product_info.descripcion:
            product_info.descripcion_gpt = self.gpt_service.sintetizar_descripcion(product_info.descripcion)
            
        # 3. Formateamos el mensaje con emojis y precios
        mensaje = format_telegram_message(product_info)

        # 4. Elegimos automáticamente las mejores categorías del catálogo
        try:
            catalog = self.category_repository.load_catalog()
            categorias_disponibles = catalog.to_sorted_list()
            
            # La IA intenta elegir las categorías más adecuadas
            raw_categories = self.gpt_service.seleccionar_categorias(
                titulo=product_info.titulo or "",
                descripcion_resumida=product_info.descripcion_gpt or "",
                categorias_disponibles=categorias_disponibles
            )
            
            categorias_elegidas = [normalize_hashtag(c) for c in (raw_categories or []) if normalize_hashtag(c)]
            
            # Si la IA no se decide, usamos el buscador de palabras clave tradicional
            if not categorias_elegidas:
                categorias_elegidas = self._fallback_select_categories(
                    f"{product_info.titulo} {product_info.descripcion_gpt}",
                    categorias_disponibles
                )
                
            if categorias_elegidas:
                mensaje = mensaje.rstrip("\n") + "\n\n" + " ".join(categorias_elegidas)
                
        except Exception:
            pass
        
        return {"text": mensaje, "product": product_info}
