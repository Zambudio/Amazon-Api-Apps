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
