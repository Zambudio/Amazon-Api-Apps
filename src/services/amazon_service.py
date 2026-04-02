import logging
from typing import Optional
from src.integrations.amazon import amazon_api
from src.domain.entities import ProductInfo

logger = logging.getLogger(__name__)

class AmazonService:
    """
    Servicio que actúa como fachada para la integración con Amazon.
    Desacopla la lógica de negocio del script concreto de la API.
    """
    
    @staticmethod
    def get_product(url_or_asin: str) -> Optional[ProductInfo]:
        """
        Consulta la API de Amazon y devuelve un objeto ProductInfo 
        con toda la información disponible (título, precio, descripción, imágenes).
        """
        return amazon_api.get_product(url_or_asin)
