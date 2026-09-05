"""
Reglas de Formato para Hashtags
Este archivo contiene la lógica para "limpiar" y estandarizar los hashtags. 
Se asegura de que todos los hashtags empiecen por '#' y tengan un formato 
visual consistente (ej: #Ejemplo), facilitando la búsqueda en Telegram.
"""

import re
from typing import Set

# Expresión regular para encontrar hashtags válidos en un texto
HASHTAG_PATTERN = re.compile(r"(?<!\w)#(\w+)", flags=re.ASCII)


def normalize_hashtag(tag: str) -> str:
    """
    Convierte cualquier texto en un hashtag válido.
    Ejemplo: 'hogar' -> '#Hogar', '#limpieza' -> '#Limpieza'
    """
    raw = (tag or "").strip()
    if not raw:
        return ""

    # Quitamos el '#' inicial si ya lo trae para procesar solo el texto
    if raw.startswith("#"):
        raw = raw[1:]

    # Solo permitimos letras, números y guiones bajos
    normalized = "".join(ch for ch in raw if ch.isalnum() or ch == "_")
    if not normalized:
        return ""

    # Ponemos la primera letra en Mayúscula (CamelCase básico)
    normalized = normalized[0].upper() + normalized[1:]
    return f"#{normalized}"


def is_valid_hashtag(tag: str) -> bool:
    """Comprueba si un texto cumple estrictamente con el formato de hashtag."""
    normalized = normalize_hashtag(tag)
    if not normalized:
        return False
    return bool(HASHTAG_PATTERN.fullmatch(normalized))


def extract_hashtags(text: str) -> Set[str]:
    """Busca y extrae todos los hashtags presentes en un bloque de texto."""
    if not text:
        return set()

    tags = set()
    for match in HASHTAG_PATTERN.findall(text):
        normalized = normalize_hashtag(match)
        if normalized:
            tags.add(normalized)
    return tags
