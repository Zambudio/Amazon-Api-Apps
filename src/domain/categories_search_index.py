"""
Mapeo de Categorías a SearchIndex de Amazon
Este archivo traduce nombres de categoría "humanos" (como los que usamos en
Telegram, ej. "Videojuegos") al código SearchIndex que espera la API de
Amazon para buscar productos de esa categoría. NO tiene relación con las
categorías/hashtags de data/categories.json, que son etiquetas de Telegram.
"""

import unicodedata

# "Computers" y "VideoGames" están verificados en vivo contra www.amazon.es
# (devuelven resultados reales). "Electronics" es el nombre oficial documentado
# por Amazon pero todavía no se ha probado en vivo.
#
# Las tres últimas usan browse_node_id en vez de search_index: en amazon.es
# "Electronics" es un SearchIndex demasiado amplio y agruparía TV, móviles y
# audio en los mismos resultados. Los IDs de nodo se obtuvieron inspeccionando
# el campo browseNodeInfo de resultados reales de búsqueda (no hay forma de
# consultarlos por nombre directamente), y están verificados en vivo:
#   - Televisores: nodo específico (no existe un nodo combinado "home cinema y películas").
#   - Mobile and Communication: nodo padre de "Móviles y smartphones libres", incluye accesorios.
#   - Audio & Sound: nodo padre de "Auriculares", incluye altavoces (ej. JBL Charge 6).
CATEGORY_SEARCH_MAP: dict[str, dict] = {
    "informatica y software": {"search_index": "Computers", "browse_node_id": None},
    "videojuegos": {"search_index": "VideoGames", "browse_node_id": None},
    "electronica": {"search_index": "Electronics", "browse_node_id": None},
    "tv, home cinema y peliculas": {"search_index": None, "browse_node_id": "934359031"},
    "moviles y accesorios": {"search_index": None, "browse_node_id": "205575109031"},
    "auriculares, altavoces y musica": {"search_index": None, "browse_node_id": "205575105031"},
}

# Etiquetas legibles (con acentos) para desplegables de UI. Cada una es válida
# como entrada de resolve_category(), que normaliza mayúsculas/acentos.
CATEGORY_DISPLAY_NAMES: list[str] = [
    "Informática y software",
    "Videojuegos",
    "Electrónica",
    "TV, home cinema y películas",
    "Móviles y accesorios",
    "Auriculares, altavoces y música",
]


def _normalizar(nombre: str) -> str:
    """Pasa a minúsculas y elimina acentos para poder comparar nombres de forma flexible."""
    sin_acentos = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode("ascii")
    return sin_acentos.strip().lower()


def resolve_category(nombre: str) -> dict:
    """Busca la categoría por nombre (ignorando mayúsculas/acentos) y devuelve su configuración de búsqueda."""
    clave = _normalizar(nombre)
    if clave not in CATEGORY_SEARCH_MAP:
        disponibles = ", ".join(sorted(CATEGORY_SEARCH_MAP.keys()))
        raise ValueError(f"Categoría desconocida: '{nombre}'. Disponibles: {disponibles}")
    return CATEGORY_SEARCH_MAP[clave]
