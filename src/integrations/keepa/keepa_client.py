"""
Integración con la API de datos de Keepa.

Fachada sobre la librería `keepa` (keepa_api_backend) que expone el histórico
de precios de un conjunto de ASINs en formato (tiempos, precios), listo para
que la capa de dominio (keepa_metrics) calcule métricas. Implementa el puerto
KeepaRepository de src/use_cases/ports/.

Reglas de integración (ver AGENTS.md): toca una API externa, así que captura
los errores de red/API y los traduce a `None` + log. La API de datos de Keepa
es de pago: la clave se lee de Config.KEEPA_API_KEY (variable KEEPA_API_KEY
en .env) y, sin ella, el cliente queda "no disponible" (get_historial → None).
"""

import logging
from typing import Optional

import keepa

from src.config.settings import Config
from src.use_cases.ports.keepa_repository import KeepaRepository

logger = logging.getLogger(__name__)

# Máximo de ASINs que acepta una petición product de Keepa (assert de la librería).
_MAX_ASINS_POR_PETICION = 100
# Por tamaño de respuesta usamos un chunk más conservador con history=True.
_CHUNK = 50

# Dominio de Amazon (España) por defecto.
_DOMINIO_DEFECTO = "es"


class KeepaClient(KeepaRepository):
    """Cliente Keepa con por-por ASIN: serie de precio nuevo (NEW o AMAZON)."""

    def __init__(self, api_key: Optional[str] = None, domain: str = _DOMINIO_DEFECTO):
        self._domain = domain
        self._api = None
        try:
            clave = api_key if api_key is not None else Config.KEEPA_API_KEY
            if clave:
                self._api = keepa.Keepa(clave)
            else:
                logger.warning("Sin KEEPA_API_KEY: el filtrado Keepa no estará disponible.")
        except Exception as e:
            logger.error("No se pudo inicializar el cliente de Keepa: %s", e)
            self._api = None

    @property
    def disponible(self) -> bool:
        """True si hay clave de API y el cliente se inicializó correctamente."""
        return self._api is not None

    def obtener_historial(self, asins: list[str], dias: int = 90) -> Optional[dict]:
        """
        Consulta el histórico de los `dias` últimos días de cada ASIN.

        Devuelve {asin: (tiempos, precios)} o None si falló la consulta. La
        serie usada es NEW (precio nuevo más bajo del marketplace, que incluye
        a Amazon cuando es el más barato) con fallback a AMAZON.
        """
        if not self._api:
            return None
        if not asins:
            return {}

        resultado: dict = {}
        try:
            for inicio in range(0, len(asins), _CHUNK):
                lote = asins[inicio:inicio + _CHUNK]
                productos = self._api.query(
                    lote,
                    domain=self._domain,
                    history=True,
                    days=dias,
                    progress_bar=False,
                )
                for producto in productos or []:
                    if not producto:
                        continue
                    serie = self._serie_utilizable(producto)
                    if serie is not None:
                        resultado[producto["asin"]] = serie
        except Exception as e:
            logger.error("Error consultando el histórico de Keepa: %s", e)
            return None
        return resultado

    def _serie_utilizable(self, producto: dict) -> Optional[tuple]:
        """Extrae (tiempos, precios) de la serie NEW (o AMAZON) de un producto."""
        datos = producto.get("data")
        if not datos:
            return None
        if "NEW" in datos and len(datos["NEW"]) > 0:
            return tuple(datos["NEW_time"]), tuple(datos["NEW"])
        if "AMAZON" in datos and len(datos["AMAZON"]) > 0:
            return tuple(datos["AMAZON_time"]), tuple(datos["AMAZON"])
        return None
