"""
Integración con Amazon Creators API (v3.2)
Este archivo gestiona la comunicación con la API oficial de Amazon para obtener 
toda la información de un producto (título, precio, imágenes, etc.) a partir 
de su ASIN o su URL. Incluye lógica para limpiar títulos y manejar errores.
"""

import sys
import json
import os
import re
from dataclasses import dataclass, field
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configuración para que los caracteres especiales se vean bien en la consola de Windows
if sys.stdout is not None and getattr(sys.stdout, 'encoding', None) != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, Exception):
        pass

# Intentamos importar la SDK de Amazon. Si no está, usamos clases "Mock" para que el programa no explote.
try:
    from creatorsapi_python_sdk import DefaultApi as AmazonCreatorsApi
    try:
        from creatorsapi_python_sdk import Country
    except ImportError:
        class Country:
            ES = "ES"
    from creatorsapi_python_sdk.models.get_items_resource import GetItemsResource
except ImportError:
    AmazonCreatorsApi = None
    class Country: ES = "ES"
    class GetItemsResource: 
        ITEM_INFO_DOT_TITLE = "ItemInfo.Title"
        def __getattr__(cls, name): return name
    GetItemsResource = GetItemsResource()


# Credenciales obtenidas de variables de entorno (.env)
CREDENTIAL_ID     = os.getenv("AMAZON_CLIENT_ID",     "TU_CREDENTIAL_ID")
CREDENTIAL_SECRET = os.getenv("AMAZON_CLIENT_SECRET",  "TU_CREDENTIAL_SECRET")
AFFILIATE_TAG     = os.getenv("AMAZON_AFFILIATE_TAG",  "buenchollo0b-21")
API_VERSION       = "3.2"
COUNTRY           = Country.ES

# Lista de recursos que le pedimos a Amazon para cada producto
RESOURCES = [
    GetItemsResource.ITEM_INFO_DOT_TITLE,
    GetItemsResource.ITEM_INFO_DOT_BY_LINE_INFO,
    GetItemsResource.ITEM_INFO_DOT_FEATURES,
    GetItemsResource.ITEM_INFO_DOT_PRODUCT_INFO,
    GetItemsResource.ITEM_INFO_DOT_TECHNICAL_INFO,
    GetItemsResource.ITEM_INFO_DOT_CLASSIFICATIONS,
    GetItemsResource.IMAGES_DOT_PRIMARY_DOT_LARGE,
    GetItemsResource.IMAGES_DOT_VARIANTS_DOT_LARGE,
    GetItemsResource.OFFERS_V2_DOT_LISTINGS_DOT_PRICE,
    GetItemsResource.OFFERS_V2_DOT_LISTINGS_DOT_AVAILABILITY,
    GetItemsResource.OFFERS_V2_DOT_LISTINGS_DOT_DEAL_DETAILS,
    GetItemsResource.OFFERS_V2_DOT_LISTINGS_DOT_IS_BUY_BOX_WINNER,
    GetItemsResource.OFFERS_V2_DOT_LISTINGS_DOT_MERCHANT_INFO,
    GetItemsResource.CUSTOMER_REVIEWS_DOT_STAR_RATING,
    GetItemsResource.CUSTOMER_REVIEWS_DOT_COUNT,
    GetItemsResource.BROWSE_NODE_INFO_DOT_BROWSE_NODES,
]

@dataclass
class ProductInfo:
    """Objeto que contiene toda la información útil de un producto de Amazon."""
    asin: str = ""
    url_afiliado: str = ""
    titulo: str = ""
    marca: str = ""
    categoria: str = ""
    descripcion: list[str] = field(default_factory=list)
    descripcion_gpt: Optional[str] = None
    precio_actual: Optional[float] = None
    precio_anterior: Optional[float] = None
    descuento_porcentaje: Optional[int] = None
    moneda: str = "EUR"
    disponibilidad: str = ""
    es_oferta: bool = False
    badge_oferta: str = ""
    fin_oferta: Optional[str] = None
    valoracion: Optional[float] = None
    num_valoraciones: Optional[int] = None
    imagen_principal: str = ""
    imagenes_extra: list[str] = field(default_factory=list)
    vendedor: str = ""
    prime: bool = False
    caracteristicas: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    def resumen(self) -> str:
        """Genera un resumen visual del producto para mostrar en consola."""
        sep = "=" * 62
        lines = [
            sep,
            f"  ASIN         : {self.asin}",
            f"  Título       : {self.titulo[:75]}{'...' if len(self.titulo) > 75 else ''}",
            f"  Marca        : {self.marca or '-'}",
            f"  Categoría    : {self.categoria or '-'}",
        ]
        if self.precio_actual:
            lines.append(f"  Precio actual: {self.precio_actual:.2f} {self.moneda}")
        else:
            lines.append("  Precio actual: No disponible")

        if self.precio_anterior:
            lines.append(f"  Precio antes : {self.precio_anterior:.2f} {self.moneda}")

        if self.descuento_porcentaje:
            lines.append(f"  Descuento    : -{self.descuento_porcentaje}%  ← OFERTA")

        lines += [
            f"  Disponible   : {self.disponibilidad or '-'}",
            f"  Vendedor     : {self.vendedor or '-'}",
            f"  Valoración   : {self.valoracion}/5 ({self.num_valoraciones:,} reseñas)" if self.valoracion else "  Valoración   : -",
            f"  Link afiliado: {self.url_afiliado[:70]}...",
        ]
        lines.append(sep)
        return "\n".join(lines)


def _safe(obj, *attrs, default=None):
    """Navega por objetos anidados de forma segura para evitar errores 'NoneType'."""
    for attr in attrs:
        if obj is None:
            return default
        obj = getattr(obj, attr, None)
    return obj if obj is not None else default


def extraer_producto(item, tag: str) -> ProductInfo:
    """Convierte un resultado bruto de la API de Amazon en nuestro objeto ProductInfo."""
    p = ProductInfo()
    p.asin = item.asin or ""
    p.url_afiliado = item.detail_page_url or f"https://www.amazon.es/dp/{p.asin}?tag={tag}"

    # Limpieza del título: nos quedamos solo con la parte descriptiva antes de guiones o comas largas
    raw_title = _safe(item, "item_info", "title", "display_value", default="")
    if raw_title:
        p.titulo = re.split(r'(?:,\s+|\s+-\s+|\s+–\s+|\s+—\s+|\s+_\s+|\s+\|\s+|\|)', raw_title)[0].strip()

    p.marca = _safe(item, "item_info", "by_line_info", "brand", "display_value", default="")

    try:
        nodes = item.browse_node_info.browse_nodes
        if nodes:
            p.categoria = " > ".join([n.display_name for n in nodes if n.display_name][:3])
    except Exception:
        pass

    try:
        p.imagen_principal = item.images.primary.large.url or ""
        variants = item.images.variants
        if variants:
            p.imagenes_extra = [v.large.url for v in variants if _safe(v, "large", "url")][:6]
    except Exception:
        pass

    # Extracción de precios y detalles de oferta
    try:
        listings = item.offers_v2.listings
        if listings:
            listing = next((l for l in listings if getattr(l, "is_buy_box_winner", False)), listings[0])

            price_obj = _safe(listing, "price", "money")
            if price_obj:
                p.precio_actual = getattr(price_obj, "amount", None)
                p.moneda = getattr(price_obj, "currency", "EUR")

            saving_basis = _safe(listing, "price", "saving_basis", "money")
            if saving_basis:
                p.precio_anterior = getattr(saving_basis, "amount", None)

            savings_pct = _safe(listing, "price", "savings", "percentage")
            if savings_pct:
                p.descuento_porcentaje = int(savings_pct)

            deal_badge = _safe(listing, "deal_details", "badge")
            if deal_badge:
                p.badge_oferta = deal_badge
                p.es_oferta = True

            p.fin_oferta = _safe(listing, "deal_details", "end_time")
            p.vendedor = _safe(listing, "merchant_info", "name", default="")
    except Exception:
        pass

    return p


def extract_asin_from_url(url: str) -> Optional[str]:
    """Busca un ASIN de 10 caracteres en una URL de Amazon, incluso tras redirecciones."""
    m = re.search(r'/(?:dp|gp/product|product)/([A-Z0-9]{10})', url)
    if m:
        return m.group(1)
        
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            final_url = response.geturl()
            m = re.search(r'/(?:dp|gp/product|product)/([A-Z0-9]{10})', final_url)
            if m:
                return m.group(1)
    except Exception:
        pass
    return None

def get_product(url_or_asin: str) -> Optional[ProductInfo]:
    """Función principal para obtener datos de un producto desde Amazon."""
    if url_or_asin.startswith("http"):
        asin = extract_asin_from_url(url_or_asin)
    else:
        asin = url_or_asin.strip().upper()

    if not asin:
        return None

    api = AmazonCreatorsApi(
        credential_id=CREDENTIAL_ID,
        credential_secret=CREDENTIAL_SECRET,
        version=API_VERSION,
        tag=AFFILIATE_TAG,
        country=COUNTRY,
        throttling=1,
    )

    try:
        items = api.get_items([asin], resources=RESOURCES)
        if not items:
            return None
        return extraer_producto(items[0], AFFILIATE_TAG)
    except Exception as e:
        print(f"[✗] Error de API: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Uso: python amazon_api.py <url_amazon_o_asin>")
        sys.exit(1)
    product = get_product(sys.argv[1])
    if product:
        print(product.resumen())

if __name__ == "__main__":
    main()
