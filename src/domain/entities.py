"""
Entidades de Dominio
Este archivo define los modelos de datos principales (clases) que se mueven 
por todo el sistema. Sirve para que todas las capas del programa hablen el 
mismo idioma y entiendan qué es un Producto o un Borrador de Post.
"""

from dataclasses import dataclass, field
from typing import Optional, List

# Reutilizamos el modelo de datos de Amazon API para mantener la compatibilidad.
# Esto asegura que la información extraída de Amazon se ajuste a nuestro sistema.
from src.integrations.amazon.amazon_api import ProductInfo

@dataclass
class PostDraft:
    """
    Representa un borrador de mensaje listo para ser publicado en Telegram.
    Contiene el texto ya formateado, la imagen seleccionada y su estado actual.
    """
    id: str
    product_asin: str
    formatted_text: str
    image_url: Optional[str] = None
    # Estados posibles: DRAFT (Borrador), PUBLISHED (Publicado), REJECTED (Rechazado)
    status: str = "DRAFT" 
