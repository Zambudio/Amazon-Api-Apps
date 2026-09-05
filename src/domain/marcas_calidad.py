"""
Marcas de calidad (para el filtrado de chollos)
Lista curada de marcas tech con buena reputación en Amazon España, pensada
para quedarse con ofertas de marcas fiables y descartar imitaciones/genéricos.
Es una lista global por ahora (independiente de la categoría): si hace falta
perfeccionarla, se puede ampliar MARCAS_CALIDAD o especializarla por categoría.

La comparación normaliza la marca que da Amazon (quita sufijos legales/técnicos
como "Inc.", "Ltd.", "Electronics", "Technologies"... y espacios) para que
"SONY", "Sony Corp." o "Sony Electronics" matcheen con "sony".
"""

from typing import Optional

import unicodedata as _unicodedata


def _normalizar_nombre(nombre: str) -> str:
    """Normaliza un nombre para comparación: minúsculas y sin acentos."""
    return (
        _unicodedata.normalize("NFKD", nombre)
        .encode("ascii", "ignore")
        .decode("ascii")
        .strip()
        .lower()
    )


# Marcas consideradas de calidad (en minúsculas, sin sufijos). Añadir o quitar
# según criterio del usuario: esto es lo que se usa con el filtro de calidad.
MARCAS_CALIDAD = frozenset({
    # Electrónica de consumo y movilidad
    "apple", "samsung", "google", "xiaomi", "huawei", "oneplus", "oppo",
    "nothing", "motorola", "sony", "lg", "panasonic", "philips", "sharp",
    "tcl", "amazon", "hisense", "toshiba", "poco", "realme", "honor", "redmi",
    # Informática y componentes
    "asus", "acer", "lenovo", "dell", "hp", "msi", "gigabyte", "razer",
    "corsair", "kingston", "crucial", "intel", "amd", "nvidia", "logitech",
    "trust", "tp-link", "netgear", "asrock", "fractal design", "be quiet",
    "noctua", "arctic", "steelseries", "hyperx", "corsair", "roccat",
    "coolermaster", "cooler master", "cool master",
    "logitech g", "rog", "aorus", "predator", "nitro",
    # Almacenamiento
    "western digital", "seagate", "sandisk", "samsung", "crucial",
    "kingston", "sabrent", "silicon power",
    # Audio
    "bose", "jbl", "sennheiser", "sonos", "marshall", "audio-technica",
    "edifier", "anker", "jlab", "soundcore", "jabra", "plantronics",
    "beyerdynamic", "shure", "focal", "wharfedale", "harman kardon",
    # Accesorios y carga
    "belkin", "baseus", "ugreen", "aukey", "ravpower", "eurocase",
    # Fotografía, GPS y dronas
    "canon", "nikon", "fujifilm", "gopro", "dji", "garmin", "tomtom",
    "olympus", "sigma", "insta360", "polaroid",
    # Impresión y ofimática
    "epson", "brother", "canon", "hp",
    # Wearables y salud
    "fitbit", "garmin", "samsung", "apple", "huawei", "xiaomi", "amazfit",
    "polar",
    # Redes y conectividad
    "tp-link", "netgear", "asus", "ubiquiti", "d-link", "linksys",
    # Consolas y gaming (sub-marcas)
    "nintendo", "microsoft", "sony",
    # Smart home y domótica
    "philips", "ikea", "tuya", "aqara", "tuya", "govee", "tapo", "eufy",
    "sonoff", "ewpe", "roborock", "dreame", "dyson", "irobot", "miele",
    # Software y suscripciones
    "microsoft", "adobe", "bitdefender", "kaspersky", "mcafee", "norton",
    "corel",
    # Almacenamiento y memoria
    "lexar", "pny", "sabrent", "silicon power", "reletech",
    # Redes y conectividad extra
    "tenda", "cudy", "tp-link", "netgear", "d-link", "linksys", "ubiquiti",
    # Consumibles de impresión
    "ricoh", "phomemo", "hippio",
    # Telecomunicaciones
    "gigaset", "motorola", "kenwood", "icom", "midland", "baofeng",
    # eBooks
    "kobo", "pocketbook", "kindle",
})

# Sufijos que Amazon suele añadir a la marca y que no aportan información.
_SUFIJOS = (
    ", inc", ", inc.", ", llc", ", ltd", ", ltd.", ", corp", ", corp.",
    ", co.", ", s.a.", ", s.l.", ", s.l.u.", ", gmbh", ", spa",
    " inc.", " incorporated", " corporation", " llc", " ltd", " ltd.",
    " gmbh", " co.", " company", " technologies", " technology", " tech",
    " electronics", " digital", " products", " group", " s.a.", " s.l.",
    " s.l.u.", " spa", " corp", " corporation", " limited", " pty ltd",
    " co ltd",
)

# ── Mapa de marcas candidatas por categoría (claves normalizadas) ─────────
# Se usa en el barrido por marcas: por cada categoría se barren solo las
# marcas de calidad relevantes a esa categoría (evita buscar "Canon" en
# "Pilas y cargadores"). Las claves coinciden con las de CATEGORY_SEARCH_MAP
# en categories_search_index.py (normalizadas, sin acentos).
# Las marcas se escriben en minúsculas; se cruzan con MARCAS_CALIDAD en
# runtime para validar que siguen en la lista curada.

_MARCAS_POR_CATEGORIA: dict[str, tuple[str, ...]] = {
    "informatica y software": (
        "asus", "acer", "lenovo", "dell", "hp", "msi", "gigabyte", "razer",
        "corsair", "kingston", "crucial", "intel", "amd", "nvidia", "logitech",
        "tp-link", "netgear", "fractal design", "be quiet", "noctua", "arctic",
        "steelseries", "hyperx", "roccat", "coolermaster", "western digital",
        "seagate", "sandisk", "sabrent", "silicon power",
    ),
    "videojuegos": (
        "sony", "microsoft", "nintendo", "razer", "logitech", "logitech g",
        "corsair", "hyperx", "steelseries", "asus", "rog", "msi",
        "gigabyte", "aorus", "predator", "kingston", "crucial",
    ),
    "electronica": (
        "sony", "samsung", "lg", "philips", "panasonic", "sharp", "tcl",
        "hisense", "toshiba", "amazon", "anker", "belkin", "ugreen", "baseus",
    ),
    "tv, home cinema y peliculas": (
        "sony", "samsung", "lg", "philips", "panasonic", "hisense", "tcl",
        "toshiba", "amazon", "shure", "jbl", "bose", "sonos",
    ),
    "moviles y accesorios": (
        "apple", "samsung", "google", "xiaomi", "huawei", "oneplus", "motorola",
        "nothing", "oppo", "sony", "anker", "baseus", "ugreen", "belkin",
        "samsung", "spigen", "esr",
    ),
    "auriculares, altavoces y musica": (
        "sony", "samsung", "jbl", "bose", "sennheiser", "sonos", "marshall",
        "audio-technica", "edifier", "anker", "jlab", "soundcore", "jabra",
        "beyerdynamic", "shure", "focal", "wharfedale", "harman kardon",
        "marshall", "google", "apple", "xiaomi",
    ),
    "tabletas": (
        "apple", "samsung", "google", "xiaomi", "lenovo", "huawei", "amazon",
        "microsoft", "asus", "acer",
    ),
    "informatica": (
        "asus", "acer", "lenovo", "dell", "hp", "msi", "gigabyte", "razer",
        "corsair", "kingston", "crucial", "intel", "amd", "nvidia", "logitech",
        "tp-link", "netgear", "fractal design", "be quiet", "noctua", "arctic",
        "steelseries", "hyperx", "roccat", "coolermaster", "western digital",
        "seagate", "sandisk", "sabrent", "silicon power",
    ),
    "tecnologia para vestir": (
        "apple", "samsung", "google", "garmin", "fitbit", "huawei", "xiaomi",
        "amazfit", "polar", "sony", "fitbit", "garmin",
    ),
    "equipos de audio y hi-fi": (
        "sony", "samsung", "jbl", "bose", "sennheiser", "sonos", "marshall",
        "audio-technica", "edifier", "soundcore", "jabra", "beyerdynamic",
        "shure", "focal", "wharfedale", "harman kardon",
    ),
    "audio y video portatil": (
        "jbl", "sony", "bose", "marshall", "soundcore", "anker", "jlab",
        "edifier", "samsung", "apple", "xiaomi",
    ),
    "auriculares": (
        "sony", "samsung", "jbl", "bose", "sennheiser", "marshall",
        "audio-technica", "edifier", "soundcore", "jabra", "beyerdynamic",
        "shure", "anker", "jlab", "apple", "google", "nothing",
    ),
    "fotografia y videocamaras": (
        "canon", "nikon", "sony", "fujifilm", "gopro", "dji", "panasonic",
        "olympus", "sigma", "insta360", "polaroid",
    ),
    "gps y accesorios": (
        "garmin", "tomtom", "apple", "samsung", "xiaomi", "huawei",
    ),
    "accesorios de alimentacion": (
        "anker", "baseus", "ugreen", "aukey", "belkin", "ravpower", "eurocase",
        "samsung", "xiaomi", "amazon",
    ),
    "pilas y cargadores": (
        "panasonic", "duracell", "varta", "energizer", "anker", "baseus",
        "ugreen", "belkin", "amazon", "eurocase",
    ),
    "lectores de ebooks y accesorios": (
        "amazon", "kobo", "pocketbook", "sony",
    ),
    "radiocomunicacion": (
        "kenwood", "icom", "midland", "baofeng", "motorola",
    ),
    "telefonia fija y accesorios": (
        "gigaset", "panasonic", "motorola", "sony",
    ),
    "software y suscripciones": (
        "microsoft", "google", "bitdefender", "mcafee", "kaspersky",
        "norton", "adobe", "corel", "sony", "nintendo",
    ),
    "smart home y domotica": (
        "philips", "tuya", "aqara", "ikea", "roborock", "dreame", "dyson",
        "irobot", "miele", "amazon", "tapo", "eufy", "ewpe", "sonoff",
    ),
    "impresoras y consumibles": (
        "hp", "canon", "epson", "brother", "xiaomi", "phomemo", "ricoh",
        "kruger", "amazon",
    ),
    "almacenamiento y discos": (
        "western digital", "seagate", "sandisk", "kingston", "crucial",
        "samsung", "sabrent", "silicon power", "lexar", "toshiba",
    ),
    "redes y wifi": (
        "tp-link", "netgear", "asus", "linksys", "d-link", "ubiquiti",
        "xiaomi", "tenda", "amazon", "honor",
    ),
}


def marcas_para_categoria(categoria: str) -> list[str]:
    """Devuelve las marcas de calidad candidatas para una categoría.

    Normaliza la categoría (quita acentos, minúsculas) para hacer lookup en
    _MARCAS_POR_CATEGORIA. Si la categoría no está en el mapa, devuelve []
    (el llamante caerá en el barrido solo por refinements).
    Devuelve solo marcas que estén en MARCAS_CALIDAD (validación cruzada).
    """
    from src.domain.categories_search_index import resolve_category
    try:
        config = resolve_category(categoria)
    except ValueError:
        return []

    # Clave normalizada = el mismo formato que _MARCAS_POR_CATEGORIA
    clave = _normalizar_nombre(categoria)
    candidatas = _MARCAS_POR_CATEGORIA.get(clave, [])
    # Filtrar por marcas que efectivamente estén en la lista curada
    return [m for m in candidatas if m in MARCAS_CALIDAD]


def es_marca_calidad(marca: Optional[str]) -> bool:
    """True si la marca (como la devuelve Amazon) está en la lista de calidad.

    Normaliza primero: minúsculas, quita sufijos (Inc., Ltd., Electronics...),
    espacios y puntuación final. Devuelve False para marcas vacías.

    Estrategia de match (en orden):
      1. Nombre completo contra la lista.
      2. Nombre sin sufijos legales/técnicos.
      3. Fragmento anterior a la coma (p.ej. "Sony, Inc." → "sony").
      4. Primera palabra del nombre (p.ej. "Soundcore by Anker" → "soundcore"),
         solo si tiene >1 carácter para evitar falsos positivos con siglas.
    """
    if not marca:
        return False

    normalizada = marca.strip().lower()

    # 1) Nombre completo ya está en la lista (p. ej. "Western Digital").
    if normalizada in MARCAS_CALIDAD:
        return True

    # 2) Quitamos sufijos legales/técnicos. Tras CADA corte comprobamos la
    #    lista: así "Western Digital" (tras quitar ", Inc." y " Technologies")
    #    matchea ANTES de que el sufijo " digital" se lo coma.
    sin_sufijos = normalizada
    for _ in range(3):
        for sufijo in _SUFIJOS:
            if sin_sufijos.endswith(sufijo):
                sin_sufijos = sin_sufijos[: -len(sufijo)].strip()
                if sin_sufijos in MARCAS_CALIDAD:
                    return True
                break
        else:
            break
    sin_sufijos = sin_sufijos.strip("., ")

    if sin_sufijos in MARCAS_CALIDAD:
        return True

    # 3) Fragmento anterior a la coma.
    if "," in sin_sufijos:
        parte_izq = sin_sufijos.split(",")[0].strip()
        if parte_izq in MARCAS_CALIDAD:
            return True

    # 4) Primera palabra (para "Soundcore by Anker", "Logitech G Series"...).
    palabras = normalizada.split()
    if palabras and len(palabras[0]) > 1 and palabras[0] in MARCAS_CALIDAD:
        return True

    return False
