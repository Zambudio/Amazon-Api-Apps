"""
Servicio de Amazon
Este archivo actúa como un intermediario (fachada) para consultar productos 
en Amazon. Su función es aislar la lógica de negocio del resto del sistema 
de los detalles técnicos de la API de Amazon.
"""

import logging
from typing import Optional
from src.integrations.amazon import amazon_api
from src.domain.entities import ProductInfo
from src.domain.categories_search_index import resolve_category

logger = logging.getLogger(__name__)

class AmazonService:
    """
    Proporciona métodos sencillos para obtener información de productos.
    Cualquier parte del programa que necesite datos de Amazon usará este servicio.
    """

    @staticmethod
    def get_product(url_or_asin: str) -> Optional[ProductInfo]:
        """
        Busca un producto por su enlace o código ASIN y devuelve un objeto
        con toda su información (título, precio, fotos, etc.).
        """
        return amazon_api.get_product(url_or_asin)

    @staticmethod
    def search_deals(categoria: str, min_saving_percent: int = 20, item_count: int = 10, item_page: int = 1) -> list[ProductInfo]:
        """
        Busca productos en oferta dentro de una categoría (ej. "Videojuegos") y
        devuelve una lista de productos con su información (título, precio, descuento, etc.).
        """
        config = resolve_category(categoria)
        return amazon_api.search_products(
            search_index=config["search_index"],
            browse_node_id=config["browse_node_id"],
            min_saving_percent=min_saving_percent,
            item_count=item_count,
            item_page=item_page,
        )
