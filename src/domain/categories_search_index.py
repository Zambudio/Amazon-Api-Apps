"""
Mapeo de Categorías a SearchIndex de Amazon
Este archivo traduce nombres de categoría "humanos" (como los que usamos en
Telegram, ej. "Videojuegos") al código SearchIndex que espera la API de
Amazon para buscar productos de esa categoría. NO tiene relación con las
categorías/hashtags de data/categories.json, que son etiquetas de Telegram.
"""

import unicodedata

# Estrategia doble para maximizar ofertas (exploración 2026-08):
#   - SearchIndex ("Computers", "VideoGames", "Electronics"): cubre la categoría
#     completa. "Electronics" es un índice muy amplio y agrupa TV, móviles y audio.
#   - browse_node_id: nodos tecnológicos concretos del árbol de Electrónica,
#     descubiertos y VERIFICADOS en vivo (2026-08-01) ascendiendo ancestros desde
#     resultados reales. Cada nodo devuelve un ranking distinto de ofertas, así
#     que ampliar el mapa con más nodos aumenta el número de chollos únicos
#     (el buscador deduplica por ASIN entre categorías).
#   - keywords: para nichos tech sin browse_node estable (o con el índice de
#     papel mezclado), se busca por palabra clave (ej. "router wifi"). Esto
#     fue validado en vivo el 2026-08-29 (scripts/explore_search_nodes.py).
#
# Verificación en vivo de los nodos (browseNodeId): Informática=683279031,
# Tabletas=938010031, Comunicación móvil=665492031, Wearables=17425674031,
# Audio Hi-Fi=665476031, Audio portátil=665477031, Auriculares=17420905031,
# TV/vídeo/home cinema=664659031, Televisores=934359031, Fotografía=664660031,
# GPS=664661031, Alimentación=970144031, Pilas/cargadores=934120031,
# eBooks=928457031, Radiocomunicación=928459031, Telefonía fija=928458031.
CATEGORY_SEARCH_MAP: dict[str, dict] = {
    "informatica y software": {"search_index": "Computers", "browse_node_id": None},
    "videojuegos": {"search_index": "VideoGames", "browse_node_id": None},
    "electronica": {"search_index": "Electronics", "browse_node_id": None},
    "tv, home cinema y peliculas": {"search_index": None, "browse_node_id": "934359031"},
    "moviles y accesorios": {"search_index": None, "browse_node_id": "205575109031"},
    "auriculares, altavoces y musica": {"search_index": None, "browse_node_id": "205575105031"},
    "tabletas": {"search_index": None, "browse_node_id": "938010031"},
    "informatica": {"search_index": None, "browse_node_id": "683279031"},
    "tecnologia para vestir": {"search_index": None, "browse_node_id": "17425674031"},
    "equipos de audio y hi-fi": {"search_index": None, "browse_node_id": "665476031"},
    "audio y video portatil": {"search_index": None, "browse_node_id": "665477031"},
    "auriculares": {"search_index": None, "browse_node_id": "17420905031"},
    "fotografia y videocamaras": {"search_index": None, "browse_node_id": "664660031"},
    "gps y accesorios": {"search_index": None, "browse_node_id": "664661031"},
    "accesorios de alimentacion": {"search_index": None, "browse_node_id": "970144031"},
    "pilas y cargadores": {"search_index": None, "browse_node_id": "934120031"},
    "lectores de ebooks y accesorios": {"search_index": None, "browse_node_id": "928457031"},
    "radiocomunicacion": {"search_index": None, "browse_node_id": "928459031"},
    "telefonia fija y accesorios": {"search_index": None, "browse_node_id": "928458031"},
    # ── Nuevas categorías tech (verificadas 2026-08-29) ────────────────────
    # SearchIndex son índices oficiales de Amazon.es; keywords para nichos
    # sin browse_node estable. Ambas se combinan con el barrido por marcas
    # de calidad, que filtra el ruido (papelería, genéricos chinos...).
    "software y suscripciones": {"search_index": "Software", "browse_node_id": None,
                                 "keywords": None},
    "smart home y domotica": {"search_index": "Appliances", "browse_node_id": None,
                              "keywords": "smart home"},
    "impresoras y consumibles": {"search_index": None, "browse_node_id": None,
                                 "keywords": "impresora"},
    "almacenamiento y discos": {"search_index": None, "browse_node_id": None,
                                "keywords": "disco duro"},
    "redes y wifi": {"search_index": None, "browse_node_id": None,
                     "keywords": "router wifi"},
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
    "Tabletas",
    "Informática",
    "Tecnología para vestir",
    "Equipos de audio y Hi-Fi",
    "Audio y vídeo portátil",
    "Auriculares",
    "Fotografía y videocámaras",
    "GPS y accesorios",
    "Accesorios de alimentación",
    "Pilas y cargadores",
    "Lectores de eBooks y accesorios",
    "Radiocomunicación",
    "Telefonía fija y accesorios",
    "Software y suscripciones",
    "Smart home y domótica",
    "Impresoras y consumibles",
    "Almacenamiento y discos",
    "Redes y WiFi",
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
