from dataclasses import dataclass
from typing import Optional, List

# Reutilizamos el modelo de datos de Amazon API por ahora para no romper su lógica,
# pero lo importamos aquí para que el resto del sistema dependa de "domain" y no 
# directamente de "integrations", facilitando un futuro desacoplamiento.
from src.integrations.amazon.amazon_api import ProductInfo

@dataclass
class PostDraft:
    """Entidad de dominio que representa un borrador de publicación,
    sirviendo como puente antes de enviarlo a Telegram o a una base de datos.
    """
    id: str
    product_asin: str
    formatted_text: str
    image_url: Optional[str] = None
    status: str = "DRAFT" # DRAFT, PUBLISHED, REJECTED
