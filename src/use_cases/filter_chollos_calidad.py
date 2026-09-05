"""
Caso de Uso: Filtrar Chollos por Calidad (marcas)

Filtra una lista de chollos (el barrido completo de ~1200 ofertas o un JSON
cargado) para quedarse con ofertas de marcas fiables, descartando imitaciones
y genéricos sin marca reconocida. La lista de marcas está en
src/domain/marcas_calidad.py.

NOTA: este filtro es SOLO por marcas. La Amazon Creators API no devuelve la
valoración de los productos (customerReviews llega siempre null en search_items
y en get_items), así que no hay datos fiables para filtrar por estrellas; el
filtro de valoración se descartó por eso.

Es un filtro POST-BÚSQUEDA sobre la lista ya acumulada: así se mantiene la
opción de ver TODAS las ofertas (~1200, con su JSON) y, aparte, la de quedarse
con las de marcas de calidad.
"""

import logging
from typing import Optional

from src.domain.entities import ProductInfo
from src.domain.marcas_calidad import es_marca_calidad

logger = logging.getLogger(__name__)


class FilterChollosCalidadUseCase:
    """Filtra una lista de chollos dejando solo marcas de calidad."""

    def __init__(self, marca_es_calidad=es_marca_calidad):
        # Inyectable para poder probarlo sin depender de la lista global.
        self._es_marca_calidad = marca_es_calidad

    def execute(
        self,
        chollos: list[ProductInfo],
        config: Optional[dict] = None,
    ) -> list[ProductInfo]:
        """Devuelve solo los chollos de marcas de calidad.

        Con solo_marcas_calidad=False se devuelve la lista sin filtrar
        (equivalente a desactivar el filtro desde la GUI).
        """
        cfg = {**_CONFIG_DEFECTO, **(config or {})}
        solo_marcas = bool(cfg.get("solo_marcas_calidad", True))

        if not solo_marcas:
            return list(chollos)

        filtrados = [
            chollo for chollo in chollos
            if self._es_marca_calidad(chollo.marca)
        ]

        logger.info(
            "Filtro de calidad (marcas): %d de %d chollos son de marcas de calidad.",
            len(filtrados), len(chollos),
        )
        return filtrados


_CONFIG_DEFECTO = {
    "solo_marcas_calidad": True,  # True = solo marcas de la lista de calidad.
}
