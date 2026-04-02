"""
Amazon Product Info — Creators API v3.2
Uso: python amazon_api.py <url_o_asin>
     python amazon_api.py <url_o_asin> --json
Requiere: pip install python-amazon-paapi
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

# Evitar errores de codificación en consola Windows (char '→', '✓', '✗', etc.)
if sys.stdout is not None and getattr(sys.stdout, 'encoding', None) != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, io.UnsupportedOperation):
        pass

from amazon_creatorsapi import AmazonCreatorsApi, Country
from amazon_creatorsapi.models import GetItemsResource

# ──────────────────────────────────────────────
#  CONFIGURACIÓN — pon aquí tus credenciales
#  o usa variables de entorno (recomendado)
# ──────────────────────────────────────────────
CREDENTIAL_ID     = os.getenv("AMAZON_CLIENT_ID",     "TU_CREDENTIAL_ID")
CREDENTIAL_SECRET = os.getenv("AMAZON_CLIENT_SECRET",  "TU_CREDENTIAL_SECRET")
AFFILIATE_TAG     = os.getenv("AMAZON_AFFILIATE_TAG",  "buenchollo0b-21")
API_VERSION       = "3.2"   # versión Creators API activa (LWA)
COUNTRY           = Country.ES

# Recursos que queremos obtener de la API
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


# ──────────────────────────────────────────────
#  Dataclass de resultado
# ──────────────────────────────────────────────

@dataclass
class ProductInfo:
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

        if self.badge_oferta:
            lines.append(f"  Badge        : {self.badge_oferta}")

        lines += [
            f"  Disponible   : {self.disponibilidad or '-'}",
            f"  Vendedor     : {self.vendedor or '-'}",
            f"  Valoración   : {self.valoracion}/5 ({self.num_valoraciones:,} reseñas)" if self.valoracion else "  Valoración   : -",
            f"  Prime        : {'✓' if self.prime else '✗'}",
            f"  Link afiliado: {self.url_afiliado[:70]}..." if len(self.url_afiliado) > 70 else f"  Link afiliado: {self.url_afiliado}",
        ]

        if self.imagen_principal:
            lines.append(f"  Imagen       : {self.imagen_principal[:70]}...")

        if self.descripcion:
            lines.append("  Descripción  :")
            for punto in self.descripcion[:5]:
                lines.append(f"    • {punto[:100]}")

        if self.caracteristicas:
            lines.append("  Características:")
            for k, v in list(self.caracteristicas.items())[:6]:
                lines.append(f"    {k}: {v}")

        lines.append(sep)
        return "\n".join(lines)


# ──────────────────────────────────────────────
#  Helpers de extracción
# ──────────────────────────────────────────────

def _safe(obj, *attrs, default=None):
    """Accede a atributos anidados sin explosión."""
    for attr in attrs:
        if obj is None:
            return default
        obj = getattr(obj, attr, None)
    return obj if obj is not None else default


def extraer_producto(item, tag: str) -> ProductInfo:
    """Mapea un Item de la Creators API a ProductInfo."""
    p = ProductInfo()
    p.asin = item.asin or ""
    p.url_afiliado = item.detail_page_url or f"https://www.amazon.es/dp/{p.asin}?tag={tag}"

    # Título (filtrado para quedarnos solo con la primera parte antes de guiones, comas, etc)
    raw_title = _safe(item, "item_info", "title", "display_value", default="")
    if raw_title:
        # Dividir por: coma+espacio, guión entre espacios, guiones largos, underscore entre espacios o barra vertical
        p.titulo = re.split(r'(?:,\s+|\s+-\s+|\s+–\s+|\s+—\s+|\s+_\s+|\s+\|\s+|\|)', raw_title)[0].strip()
    else:
        p.titulo = ""

    # Marca
    p.marca = _safe(item, "item_info", "by_line_info", "brand", "display_value", default="")

    # Categoría
    try:
        nodes = item.browse_node_info.browse_nodes
        if nodes:
            p.categoria = " > ".join([n.display_name for n in nodes if n.display_name][:3])
    except Exception:
        pass

    # Bullet points / Features
    try:
        feats = item.item_info.features.display_values
        if feats:
            p.descripcion = [f for f in feats if f]
    except Exception:
        pass

    # Imágenes
    try:
        p.imagen_principal = item.images.primary.large.url or ""
    except Exception:
        pass
    try:
        variants = item.images.variants
        if variants:
            p.imagenes_extra = [v.large.url for v in variants if _safe(v, "large", "url")][:6]
    except Exception:
        pass

    # Valoración y reseñas
    try:
        p.valoracion = item.customer_reviews.star_rating.value
    except Exception:
        pass
    try:
        p.num_valoraciones = item.customer_reviews.count.value
    except Exception:
        pass

    # Ofertas — OffersV2
    try:
        listings = item.offers_v2.listings
        if listings:
            # Buscar primero el buybox winner
            listing = next((l for l in listings if getattr(l, "is_buy_box_winner", False)), listings[0])

            # Precio
            price_obj = _safe(listing, "price", "money")
            if price_obj:
                p.precio_actual = getattr(price_obj, "amount", None)
                p.moneda = getattr(price_obj, "currency", "EUR")

            # Precio sin descuento (saving_basis)
            saving_basis = _safe(listing, "price", "saving_basis", "money")
            if saving_basis:
                p.precio_anterior = getattr(saving_basis, "amount", None)

            # % descuento
            savings_pct = _safe(listing, "price", "savings", "percentage")
            if savings_pct:
                p.descuento_porcentaje = int(savings_pct)
            elif p.precio_actual and p.precio_anterior and p.precio_anterior > p.precio_actual:
                pct = ((p.precio_anterior - p.precio_actual) / p.precio_anterior) * 100
                p.descuento_porcentaje = round(pct)

            # Disponibilidad
            avail = _safe(listing, "availability", "message")
            if avail:
                p.disponibilidad = avail

            # Badge oferta (ej: "Oferta del día", "Tiempo limitado")
            deal_badge = _safe(listing, "deal_details", "badge")
            if deal_badge:
                p.badge_oferta = deal_badge
                p.es_oferta = True

            deal_end = _safe(listing, "deal_details", "end_time")
            if deal_end:
                p.fin_oferta = deal_end

            # Vendedor
            p.vendedor = _safe(listing, "merchant_info", "name", default="")
    except Exception as e:
        pass

    # Características técnicas
    try:
        tech = item.item_info.technical_info
        if tech and hasattr(tech, "formats") and tech.formats:
            for fmt in tech.formats.display_values:
                p.caracteristicas["Formato"] = fmt
    except Exception:
        pass

    return p


# ──────────────────────────────────────────────
#  Cliente principal
# ──────────────────────────────────────────────

def extract_asin_from_url(url: str) -> Optional[str]:
    # 1. Búsqueda rápida por regex
    m = re.search(r'/(?:dp|gp/product|product)/([A-Z0-9]{10})', url)
    if m:
        return m.group(1)
        
    try:
        # 2. Descargar la redirección o el HTML si es una URL corta/móvil
        import urllib.request
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=10) as response:
            final_url = response.geturl()
            html = response.read().decode('utf-8', errors='ignore')
            
            # Buscar en la url final tras la redirección
            m = re.search(r'/(?:dp|gp/product|product)/([A-Z0-9]{10})', final_url)
            if m:
                return m.group(1)
                
            # Buscar ASIN principal en la URL canonical del HTML
            m = re.search(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\'][^"\']*/(?:dp|gp/product|product)/([A-Z0-9]{10})', html, re.IGNORECASE)
            if m:
                return m.group(1)

            # Buscar el input escondido del ASIN principal (típico en Amazon)
            m = re.search(r'(?:name|id)=["\']ASIN["\'][^>]*value=["\']([A-Z0-9]{10})["\']', html, re.IGNORECASE)
            if m:
                return m.group(1)
                
            # Buscar el ASIN genérico si no queda otra
            m = re.search(r'ASIN(?:["\']?\s*[:=]\s*["\']?|\s+value=["\'])([A-Z0-9]{10})', html)
            if m:
                return m.group(1)
    except Exception:
        pass
        
    return None

def get_product(url_or_asin: str) -> Optional[ProductInfo]:
    """Obtiene info de un producto por URL o ASIN."""

    # Resolver ASIN
    if url_or_asin.startswith("http"):
        asin = extract_asin_from_url(url_or_asin)
    else:
        asin = url_or_asin.strip().upper()

    if not asin:
        print("[✗] No se pudo extraer el ASIN de la URL.")
        return None

    print(f"  → ASIN detectado: {asin}")

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
            print("[✗] La API no devolvió resultados para ese ASIN.")
            return None
        return extraer_producto(items[0], AFFILIATE_TAG)

    except Exception as e:
        error = str(e)
        if "AssociateNotEligible" in error:
            print("[✗] Error: AssociateNotEligible — tu cuenta de afiliado aún no tiene acceso a la API.")
            print("    Necesitas al menos 10 ventas válidas en los últimos 30 días.")
        elif "401" in error or "403" in error:
            print(f"[✗] Error de autenticación ({error}). Revisa tus credenciales.")
        else:
            print(f"[✗] Error de API: {error}")
        return None


# ──────────────────────────────────────────────
#  CLI
# ──────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Uso: python amazon_api.py <url_amazon_o_asin>")
        print("     python amazon_api.py <url> --json")
        sys.exit(1)

    entrada = sys.argv[1]
    output_json = "--json" in sys.argv

    if "amazon." not in entrada and len(entrada) != 10:
        print("[!] Aviso: la entrada no parece una URL de Amazon ni un ASIN válido.")

    product = get_product(entrada)

    if not product:
        sys.exit(1)

    if output_json:
        print(json.dumps(product.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(product.resumen())


if __name__ == "__main__":
    main()
