from typing import Optional
from src.services.amazon_service import AmazonService
from src.integrations.openai.gpt_service import GPTService
from src.formatters.telegram_formatter import format_telegram_message
from src.config.settings import Config
from src.integrations.storage.json_category_repository import JsonCategoryRepository
from src.domain.hashtag_rules import normalize_hashtag

class GeneratePostUseCase:
    """
    Caso de uso: Coge un input (URL o ASIN), extrae la información 
    y genera el formato listo para Telegram.
    """
    
    def __init__(self, amazon_service=AmazonService(), gpt_service=GPTService()):
        self.amazon_service = amazon_service
        self.gpt_service = gpt_service
        self.category_repository = JsonCategoryRepository(Config.CATEGORIES_FILE_PATH)
        
    def _fallback_select_categories(self, text: str, available: list[str]) -> list[str]:
        text_lower = text.lower()
        selected: list[str] = []

        for category in available:
            normalized = normalize_hashtag(category)
            if not normalized:
                continue

            keyword = normalized.lstrip("#").lower()
            if not keyword:
                continue

            if keyword in text_lower and normalized not in selected:
                selected.append(normalized)
                if len(selected) >= 2:
                    break

        return selected

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
            
        # 3. Generación del mensaje base
        mensaje = format_telegram_message(product_info)

        # 4. Selección de categorías desde el catálogo JSON usando GPT
        try:
            catalog = self.category_repository.load_catalog()
            categorias_disponibles = catalog.to_sorted_list()
        except Exception:
            categorias_disponibles = []

        categorias_elegidas = []
        if categorias_disponibles:
            titulo_ref = product_info.titulo or ""
            desc_ref = product_info.descripcion_gpt or (
                product_info.descripcion[0] if product_info.descripcion else ""
            )
            raw_categories = self.gpt_service.seleccionar_categorias(
                titulo=titulo_ref,
                descripcion_resumida=desc_ref,
                categorias_disponibles=categorias_disponibles,
            )
            # Normalizamos siempre para garantizar formato #Categoria
            categorias_elegidas = []
            for cat in raw_categories or []:
                normalized = normalize_hashtag(cat)
                if normalized:
                    categorias_elegidas.append(normalized)

            if not categorias_elegidas:
                categorias_elegidas = self._fallback_select_categories(
                    f"{titulo_ref} {desc_ref}",
                    categorias_disponibles,
                )

        if categorias_elegidas:
            mensaje = mensaje.rstrip("\n") + "\n\n" + " ".join(categorias_elegidas)
        
        return {"text": mensaje, "product": product_info}
