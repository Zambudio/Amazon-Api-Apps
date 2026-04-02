import os
import re
import json
import requests
from urllib.parse import urlparse, parse_qs

# =========================
# CONFIGURACIÓN
# =========================

# Guarda estas variables en tu sistema antes de ejecutar:
# Windows PowerShell:
#   $env:AMAZON_CLIENT_ID="tu_client_id"
#   $env:AMAZON_CLIENT_SECRET="tu_client_secret"
#
# Windows CMD:
#   set AMAZON_CLIENT_ID=tu_client_id
#   set AMAZON_CLIENT_SECRET=tu_client_secret

# Puedes editar estas variables para usar tus credenciales directamente en el código
CLIENT_ID_LOCAL = "amzn1.application-oa2-client.378932a5f70941a69929f4c7e1ad7fba"
CLIENT_SECRET_LOCAL = "amzn1.oa2-cs.v1.27403a43db95e669cd6863cd577e89eb7c639e260ec9be836a6f651e4342ec00"

# Mantiene la opción de usar variables de entorno (tienen prioridad si existen)
CLIENT_ID = os.getenv("AMAZON_CLIENT_ID") or CLIENT_ID_LOCAL
CLIENT_SECRET = os.getenv("AMAZON_CLIENT_SECRET") or CLIENT_SECRET_LOCAL

# Endpoint OAuth2 oficial de Amazon
# OJO: Para Europa 3.2 el SDK usa UK como endpoint de token
TOKEN_URL = "https://api.amazon.co.uk/auth/o2/token"

# OJO:
# Ajusta esta plantilla si en la documentación oficial de Creators API
# el endpoint de producto usa otra ruta base.
PRODUCT_URL_TEMPLATE = "https://api.amazon.com/creators/products/{asin}"

# Scope correcto según la especificación LWA v3.2
SCOPE = "creatorsapi::default"


# =========================
# UTILIDADES
# =========================

def extract_asin(amazon_url: str) -> str:
    """
    Extrae el ASIN desde distintas variantes de URL de Amazon.
    """
    patterns = [
        r"/dp/([A-Z0-9]{10})",
        r"/gp/product/([A-Z0-9]{10})",
        r"/product/([A-Z0-9]{10})",
    ]

    for pattern in patterns:
        match = re.search(pattern, amazon_url)
        if match:
            return match.group(1)

    # Último intento: revisar parámetros o segmentos sueltos
    parsed = urlparse(amazon_url)
    query = parse_qs(parsed.query)

    for values in query.values():
        for value in values:
            if re.fullmatch(r"[A-Z0-9]{10}", value):
                return value

    raise ValueError("No se ha podido extraer un ASIN válido de la URL.")


def get_access_token() -> str:
    """
    Obtiene access token OAuth2 usando client_credentials.
    """
    if not CLIENT_ID or not CLIENT_SECRET:
        raise RuntimeError(
            "Faltan credenciales válidas. Define CLIENT_ID y CLIENT_SECRET en el script o establécelas en las variables de entorno."
        )

    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": SCOPE,
    }

    response = requests.post(TOKEN_URL, data=data, timeout=30)
    response.raise_for_status()

    payload = response.json()
    token = payload.get("access_token")
    if not token:
        raise RuntimeError(f"No se recibió access_token. Respuesta: {payload}")

    return token


def get_product_data(asin: str, access_token: str) -> dict:
    """
    Consulta datos de producto.
    Si la ruta exacta difiere en la doc, cambia PRODUCT_URL_TEMPLATE.
    """
    url = PRODUCT_URL_TEMPLATE.format(asin=asin)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    response = requests.get(url, headers=headers, timeout=30)

    # Para depurar mejor si Amazon responde con error
    if response.status_code >= 400:
        raise RuntimeError(
            f"Error consultando producto ({response.status_code}): {response.text}"
        )

    return response.json()


def pick_first(*values):
    """
    Devuelve el primer valor no vacío.
    """
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def simplify_product_response(data: dict) -> dict:
    """
    Intenta normalizar campos típicos que te interesan para BuenChollo.
    Como no tengo aquí el esquema exacto cargado desde la doc JS,
    esto busca varias claves comunes.
    """
    # Título
    title = pick_first(
        data.get("title"),
        data.get("name"),
        data.get("productTitle"),
        data.get("itemTitle"),
    )

    # Imagen
    image = None
    images = data.get("images") or data.get("Images") or {}
    if isinstance(images, list) and images:
        first_image = images[0]
        if isinstance(first_image, dict):
            image = pick_first(
                first_image.get("url"),
                first_image.get("link"),
                first_image.get("large"),
                first_image.get("medium"),
                first_image.get("small"),
            )
        elif isinstance(first_image, str):
            image = first_image
    elif isinstance(images, dict):
        image = pick_first(
            images.get("primary"),
            images.get("large"),
            images.get("medium"),
            images.get("small"),
            images.get("url"),
        )

    # Precio actual / anterior / ahorro
    offers = data.get("offers") or data.get("Offers") or {}
    price = None
    list_price = None
    savings = None
    savings_percent = None
    offer_end = None

    # Intento 1: estructura plana
    price = pick_first(
        data.get("price"),
        data.get("currentPrice"),
        data.get("buyingPrice"),
    )
    list_price = pick_first(
        data.get("listPrice"),
        data.get("wasPrice"),
        data.get("previousPrice"),
        data.get("strikethroughPrice"),
    )
    savings = pick_first(
        data.get("savings"),
        data.get("discountAmount"),
    )
    savings_percent = pick_first(
        data.get("savingsPercentage"),
        data.get("discountPercent"),
    )
    offer_end = pick_first(
        data.get("offerEnd"),
        data.get("dealEndTime"),
        data.get("endTime"),
    )

    # Intento 2: estructura anidada de ofertas
    if isinstance(offers, dict):
        price = pick_first(
            price,
            offers.get("price"),
            offers.get("currentPrice"),
            (offers.get("Price") or {}).get("Amount"),
            (offers.get("Price") or {}).get("DisplayAmount"),
        )
        list_price = pick_first(
            list_price,
            offers.get("listPrice"),
            offers.get("savingBasis"),
            (offers.get("SavingBasis") or {}).get("Amount"),
            (offers.get("SavingBasis") or {}).get("DisplayAmount"),
        )
        savings = pick_first(
            savings,
            offers.get("savings"),
            (offers.get("Savings") or {}).get("Amount"),
            (offers.get("Savings") or {}).get("DisplayAmount"),
        )
        savings_percent = pick_first(
            savings_percent,
            (offers.get("Savings") or {}).get("Percentage"),
            offers.get("savingsPercentage"),
        )
        deal_details = offers.get("DealDetails") or {}
        offer_end = pick_first(
            offer_end,
            deal_details.get("EndTime"),
        )

    # Descripción resumida
    description = pick_first(
        data.get("description"),
        data.get("shortDescription"),
        data.get("featureBullets"),
        data.get("features"),
    )

    # URL del producto
    product_url = pick_first(
        data.get("productUrl"),
        data.get("detailPageUrl"),
        data.get("url"),
        data.get("link"),
    )

    return {
        "title": title,
        "image": image,
        "price": price,
        "list_price": list_price,
        "savings": savings,
        "savings_percent": savings_percent,
        "description": description,
        "offer_end": offer_end,
        "product_url": product_url,
        "raw": data,  # útil para inspeccionar la respuesta real
    }

def format_telegram_message(data: dict) -> str:
    """
    Toma el diccionario limpio y devuelve el texto formateado
    tal como se espera en el canal de Telegram.
    """
    title = data.get("title") or "Título no disponible"
    price = data.get("price") or "0,00 €"
    list_price = data.get("list_price") or "0,00 €"
    
    # Manejar caso de ahorro (si no hay, omitir la barra y el porcentaje o poner 0)
    savings = data.get("savings") or "0 €"
    savings_pct = data.get("savings_percent") or "0"
    
    url = data.get("product_url") or "URL_NO_DISPONIBLE"
    description = data.get("description") or "Sin descripción técnica adicional."
    
    offer_end = data.get("offer_end")
    
    # Usando los emojis de la imagen de ejemplo
    mensaje = f"🍄 {title}\n\n"
    mensaje += f"💶 Precio: {price} (antes {list_price})\n"
    mensaje += f"💰 Ahorro: {savings} | -{savings_pct}%\n\n"
    mensaje += f"🛒 {url}\n\n"
    mensaje += f"✏️ {description}\n\n"
    
    if offer_end:
        mensaje += f"⏰ Finaliza el {offer_end}\n\n"
        
    mensaje += "#CategoriaAutogenerada\n"
    
    return mensaje


def main():
    amazon_url = "https://www.amazon.es/gp/product/B0FP2T1LQH/ref=ewc_pr_img_1?smid=A1AT7YVPFBWXBL"
    #input("Pega aquí la URL del producto de Amazon: ").strip()

    try:
        asin = extract_asin(amazon_url)
        print(f"\nASIN detectado: {asin}")

        token = get_access_token()
        print("Token obtenido correctamente.")

        product_data = get_product_data(asin, token)
        result = simplify_product_response(product_data)

        print("\n=== DATOS EXTRAÍDOS ===")
        print(f"Título:          {result.get('title')}")
        print(f"Precio:          {result.get('price')}")
        print(f"Precio anterior: {result.get('list_price')}")
        
        ahorro = result.get('savings') or '0'
        porcentaje_ahorro = result.get('savings_percent') or '0'
        print(f"Ahorro:          {ahorro} (-{porcentaje_ahorro}%)")
        print(f"Imagen:          {result.get('image')}")
        print(f"Descripción:     {result.get('description')}")
        print(f"URL:             {result.get('product_url')}")
        
        print("\n=== VISTA PREVIA TELEGRAM ===")
        print(format_telegram_message(result))

    except Exception as exc:
        print(f"\nERROR: {exc}")


if __name__ == "__main__":
    main()


"""
https://www.amazon.es/Logitech-Ergon%C3%B3mico-Inal%C3%A1mbrico-Silenciosos-Compatible/dp/B0GGC3F6NS/?_encoding=UTF8&ref_=pd_hp_d_atf_dealz_mlc

https://www.amazon.es/gp/product/B0FP2T1LQH/ref=ewc_pr_img_1?smid=A1AT7YVPFBWXBL

"""
