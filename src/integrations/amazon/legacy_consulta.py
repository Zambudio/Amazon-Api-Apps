"""
Consultas de Amazon (Legacy / Deprecated)
Este archivo contiene intentos previos de conectar con Amazon de forma manual 
usando peticiones HTTP directas. Actualmente está en desuso a favor de 
amazon_api.py (que usa la SDK oficial), pero se mantiene como referencia.
"""

import os
import re
import json
import requests
from urllib.parse import urlparse, parse_qs

# Credenciales locales de respaldo
CLIENT_ID_LOCAL = "amzn1.application-oa2-client.378932a5f70941a69929f4c7e1ad7fba"
CLIENT_SECRET_LOCAL = "amzn1.oa2-cs.v1.27403a43db95e669cd6863cd577e89eb7c639e260ec9be836a6f651e4342ec00"

CLIENT_ID = os.getenv("AMAZON_CLIENT_ID") or CLIENT_ID_LOCAL
CLIENT_SECRET = os.getenv("AMAZON_CLIENT_SECRET") or CLIENT_SECRET_LOCAL

# Configuración de URLs de Amazon para peticiones directas
TOKEN_URL = "https://api.amazon.co.uk/auth/o2/token"
PRODUCT_URL_TEMPLATE = "https://api.amazon.com/creators/products/{asin}"
SCOPE = "creatorsapi::default"


def extract_asin(amazon_url: str) -> str:
    """Extrae el código ASIN de una URL usando expresiones regulares."""
    patterns = [
        r"/dp/([A-Z0-9]{10})",
        r"/gp/product/([A-Z0-9]{10})",
        r"/product/([A-Z0-9]{10})",
    ]

    for pattern in patterns:
        match = re.search(pattern, amazon_url)
        if match:
            return match.group(1)
    
    raise ValueError("No se ha podido extraer un ASIN válido.")


def get_access_token() -> str:
    """Obtiene un token de acceso temporal mediante el flujo OAuth2 de Amazon."""
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": SCOPE,
    }

    response = requests.post(TOKEN_URL, data=data, timeout=30)
    response.raise_for_status()
    return response.json().get("access_token")


def get_product_data(asin: str, access_token: str) -> dict:
    """Petición directa al endpoint de productos de Amazon."""
    url = PRODUCT_URL_TEMPLATE.format(asin=asin)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    response = requests.get(url, headers=headers, timeout=30)
    return response.json()

# ... (El resto de funciones se mantienen como lógica de mapeo manual antigua)
