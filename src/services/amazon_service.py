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
    def search_deals(
        categoria: str,
        min_saving_percent: int = 20,
        item_count: int = 10,
        item_page: Optional[int] = None,
        sort_by: Optional[str] = None,
        brand: Optional[str] = None,
    ) -> list[ProductInfo]:
        """
        Busca productos en oferta dentro de una categoría (ej. "Videojuegos") y
        devuelve una lista de productos con su información (título, precio, descuento, etc.).

        item_page indica qué página de resultados pedir a Amazon (de 1 a 10).
        Cada página trae ~10 productos como máximo; para obtener más resultados
        hay que llamar varias veces con páginas distintas.

        Args:
            sort_by: criterio de ordenación (ej. "Price:LowToHigh"). Si es None,
                     la API usa su orden por defecto ("Featured").
            brand: filtra por marca exacta (ej. "Xiaomi"). Si es None, sin filtro.
        """
        config = resolve_category(categoria)
        return amazon_api.search_products(
            search_index=config.get("search_index"),
            browse_node_id=config.get("browse_node_id"),
            keywords=config.get("keywords"),
            min_saving_percent=min_saving_percent,
            item_count=item_count,
            item_page=item_page,
            sort_by=sort_by,
            brand=brand,
        )

    @staticmethod
    def get_brand_refinements(categoria: str) -> list[str]:
        """
        Devuelve las marcas relevantes de una categoría (ej. ['XIAOMI', 'Samsung']),
        obtenidas de los refinements de la API. Se usa para barridos adicionales
        que amplíen la cobertura de chollos de una categoría. Para categorías
        que se buscan por palabra clave (sin browse_node), los refinements van
        ligados a esas palabras.
        """
        config = resolve_category(categoria)
        return amazon_api.get_brand_refinements(
            search_index=config.get("search_index"),
            browse_node_id=config.get("browse_node_id"),
            keywords=config.get("keywords"),
        )
