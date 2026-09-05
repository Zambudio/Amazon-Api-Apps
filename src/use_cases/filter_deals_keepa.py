"""
Caso de Uso: Filtrar Chollos por métricas de Keepa

Orquesta la valoración automática de una lista de chollos usando el histórico
de precios de Keepa: para cada oferta consulta su serie de precios (dominio
ES, últimos N días) y aplica unas reglas que deciden si el descuento es
"real" (precio en el mínimo del período, o caída desde un precio estable, o
tendencia descendente) o si es un señuelo (gráfica que oscila sin salir de un
rango, o bajada desde un precio inflado con precios mucho menores previos).

Las reglas y sus umbrales están en _CONFIG_DEFECTO; la GUI solo sobreescribe
las tres métricas que expone (ahorro vs media, margen sobre mínimo y días de
historia) y el resto usa estos valores sensatos. El histórico se obtiene a
través del puerto KeepaRepository (inyectado por constructor); sin datos de
Keepa (p. ej. sin API key) devuelve la lista sin filtrar para no romper el
flujo de la GUI.
"""

import logging
from typing import Optional

from src.domain.entities import ProductInfo
from src.domain.keepa_metrics import calcular_metricas
from src.use_cases.ports.keepa_repository import KeepaRepository
from src.integrations.keepa.keepa_client import KeepaClient

logger = logging.getLogger(__name__)

# Umbrales por defecto del filtro. La GUI sobreescribe ahorro_vs_media,
# margen_sobre_minimo y dias_historia; el resto son los valores "sensatos".
_CONFIG_DEFECTO = {
    "dias_historia": 90,           # Ventana a consultar (y mitad mínima exigida)
    "margen_sobre_minimo": 5,      # % sobre el mínimo para considerarlo "en el mínimo"
    "ahorro_vs_media": 10,         # % mínimo que debe estar bajo la media del período
    "bajada_reciente_pct": 15,     # % de caída reciente para la regla "estable → baja"
    "estabilidad_previo_pct": 10,  # CV máx. del período previo para esa regla
    "tendencia_descendente_pct": 15,  # % de descenso total para la regla "trend"
    "sonde_giros_max": 12,         # Más giros = gráfica "sonda" (sube/baja) → descartar
    "historico_anterior_pct": 20,  # Si antes fue ≥X% más barato → descartar
}


class FilterDealsKeepaUseCase:
    """Filtra una lista de chollos según el histórico de precios de Keepa."""

    def __init__(self, keepa_repository: Optional[KeepaRepository] = None):
        self._keepa = keepa_repository or KeepaClient()

    def execute(
        self,
        chollos: list[ProductInfo],
        config: Optional[dict] = None,
    ) -> list[ProductInfo]:
        """
        Devuelve solo los chollos cuya gráfica de precios indica descuento real.

        Sin histórico consultable (sin API key, error de red), devuelve la
        lista sin filtrar y lo registra en el log, para que el flujo de la GUI
        siga funcionando sin datos de Keepa.
        """
        cfg = {**_CONFIG_DEFECTO, **(config or {})}

        asins = [c.asin for c in chollos if c.asin]
        if not asins:
            return []

        historial = self._keepa.obtener_historial(asins, dias=int(cfg["dias_historia"]))
        if not historial:
            logger.warning(
                "Filtrado Keepa sin datos (¿API key?): %d chollos devueltos sin filtrar.",
                len(chollos),
            )
            return list(chollos)

        filtrados = []
        sin_historial = 0
        for chollo in chollos:
            serie = historial.get(chollo.asin)
            if serie is None:
                sin_historial += 1
                continue
            tiempos, precios = serie
            metricas = calcular_metricas(tiempos, precios, dias=int(cfg["dias_historia"]))
            if metricas and _cumple_reglas(metricas, cfg):
                filtrados.append(chollo)

        logger.info(
            "Filtrado Keepa: %d de %d chollos pasan (sin histórico consultable: %d).",
            len(filtrados), len(chollos), sin_historial,
        )
        return filtrados


def _cumple_reglas(m: dict, cfg: dict) -> bool:
    """Evalúa las reglas de la valoración sobre las métricas de un producto."""
    p = m["precio_actual"]
    if p <= 0:
        return False

    # La ventana debe tener al menos la mitad del período pedido: con menos
    # historia no hay forma fiable de juzgar la forma de la gráfica.
    if m["span_dias"] < int(cfg["dias_historia"]) * 0.5:
        return False

    # ── Reglas de descarte (sobrescriben cualquier pase) ──────────────────
    # 1) Ha estado mucho más barato en el período: el "chollo" actual no es un
    #    mínimo real, solo una bajada desde un precio inflado.
    if m["minimo"] < p * (1 - float(cfg["historico_anterior_pct"]) / 100):
        return False
    # 2) Gráfica "sonda": oscila constantemente sin cambiar de nivel.
    if m["giros"] > int(cfg["sonde_giros_max"]):
        return False

    # ── Reglas de pase (basta con una) ────────────────────────────────────
    cerca_minimo = p <= m["minimo"] * (1 + float(cfg["margen_sobre_minimo"]) / 100)

    caida_desde_estable = False
    if m["mediana_previa"] is not None and m["mediana_reciente"] is not None and m["mediana_previa"] > 0:
        caida = (m["mediana_previa"] - m["mediana_reciente"]) / m["mediana_previa"]
        estable = m["cv_previa"] is not None and m["cv_previa"] <= float(cfg["estabilidad_previo_pct"]) / 100
        caida_desde_estable = caida >= float(cfg["bajada_reciente_pct"]) / 100 and estable

    tendencia_descendente = False
    if m["tendencia_rel"] is not None:
        tendencia_descendente = m["tendencia_rel"] <= -float(cfg["tendencia_descendente_pct"]) / 100

    if not (cerca_minimo or caida_desde_estable or tendencia_descendente):
        return False

    # Endurecedor opcional: si se configura ahorro vs media > 0, el precio
    # actual debe estar por debajo de la media del período ese porcentaje.
    ahorro = float(cfg["ahorro_vs_media"])
    if ahorro > 0 and p > m["media"] * (1 - ahorro / 100):
        return False

    return True
