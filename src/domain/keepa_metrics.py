"""
Métricas puras de una serie de precios de Keepa.

Funciones sin efectos ni I/O: reciben una serie de (tiempos, precios) y
devuelven métricas numéricas (mínimo, media, mediana, pendiente, giros...).
Así la lógica de "qué forma tiene la gráfica" es testeable sin red ni API.

La serie de precios de Keepa usa -1 / NaN para "sin oferta" (stock agotado):
esos puntos se descartan antes de calcular nada. Los tiempos pueden ser
datetime (to_datetime=True de la librería keepa) o milisegundos unix.
"""

import math
from datetime import datetime, timedelta
from typing import Optional, Sequence, Tuple

# Ventana "reciente" para detectar la caída desde un precio estable: son los
# últimos N días (lo que se considera "ahora" frente al resto de la serie).
DIAS_RECIENTES_CAIDA = 7


def _es_precio_valido(precio) -> bool:
    """True si el precio es un número finito positivo (no NaN, -1 ni 0)."""
    try:
        valor = float(precio)
    except (TypeError, ValueError):
        return False
    return math.isfinite(valor) and valor > 0


def _a_datetime(valor) -> Optional[datetime]:
    """Normaliza un timestamp (datetime o milisegundos unix) a datetime."""
    if isinstance(valor, datetime):
        return valor
    try:
        return datetime.fromtimestamp(float(valor) / 1000)
    except (TypeError, ValueError, OSError, OverflowError):
        return None


def limpiar_serie(
    tiempos: Sequence,
    precios: Sequence,
    dias: int = 90,
    ahora: Optional[datetime] = None,
) -> Tuple[list, list]:
    """Devuelve (tiempos, precios) limitados a los últimos `dias`, sin puntos
    sin oferta y ordenados cronológicamente. Listas vacías si no hay nada."""
    if ahora is None:
        ahora = datetime.now()
    limite = ahora - timedelta(days=dias)

    pares = []
    for t, p in zip(tiempos, precios):
        if not _es_precio_valido(p):
            continue
        ts = _a_datetime(t)
        if ts is None or ts < limite:
            continue
        pares.append((ts, float(p)))

    pares.sort(key=lambda x: x[0])
    if not pares:
        return [], []
    return [x[0] for x in pares], [x[1] for x in pares]


def span_dias(tiempos: Sequence) -> float:
    """Días entre la primera y la última medición (0 si hay menos de 2)."""
    if len(tiempos) < 2:
        return 0.0
    return (tiempos[-1] - tiempos[0]).total_seconds() / 86400.0


def precio_actual(precios: Sequence) -> float:
    return float(precios[-1])


def minimo(precios: Sequence) -> float:
    return float(min(precios))


def maximo(precios: Sequence) -> float:
    return float(max(precios))


def media(precios: Sequence) -> float:
    return float(sum(precios) / len(precios))


def mediana(precios: Sequence) -> float:
    orden = sorted(precios)
    n = len(orden)
    if n % 2 == 1:
        return float(orden[n // 2])
    return float((orden[n // 2 - 1] + orden[n // 2]) / 2)


def coeficiente_variacion(precios: Sequence) -> Optional[float]:
    """Desviación típica relativa a la media (0 = totalmente estable).
    None si la media no es positiva (no tiene sentido relativizar)."""
    m = media(precios)
    if m <= 0:
        return None
    varianza = sum((x - m) ** 2 for x in precios) / len(precios)
    return math.sqrt(varianza) / m


def subserie_por_ventana(
    tiempos: Sequence, precios: Sequence, dias_finales: int
) -> Tuple[list, list, list, list]:
    """Divide la serie en (previa, reciente), donde "reciente" son los últimos
    `dias_finales` días y "previa" el resto. La parte previa puede quedar vacía
    si toda la serie cae dentro de la ventana reciente."""
    corte = tiempos[-1] - timedelta(days=dias_finales)
    idx = 0
    while idx < len(tiempos) and tiempos[idx] < corte:
        idx += 1
    return list(tiempos[:idx]), list(precios[:idx]), list(tiempos[idx:]), list(precios[idx:])


def pendiente_relativa(tiempos: Sequence, precios: Sequence) -> Optional[float]:
    """Pendiente de regresión lineal (precio vs. posición en la serie)
    normalizada por la media: devuelve la variación RELATIVA esperada a lo
    largo de toda la ventana (negativa = descendente). None si no hay datos
    suficientes o la media no es positiva."""
    n = len(precios)
    if n < 2:
        return None
    m = media(precios)
    if m <= 0:
        return None

    xs = [float(i) for i in range(n)]
    mx = sum(xs) / n
    my = m
    denom = sum((x - mx) ** 2 for x in xs)
    if denom == 0:
        return None
    pendiente = sum((x - mx) * (p - my) for x, p in zip(xs, precios)) / denom
    return pendiente * n / m


def num_giros(precios: Sequence, umbral_pct: float = 1.0) -> int:
    """Nº de cambios de dirección en la serie, indicador de "sonda" (la gráfica
    sube y baja constantemente para parecer que está en oferta).

    Solo cuenta movimientos que superen `umbral_pct` % del precio medio, para
    que el ruido de redondeo no genere giros falsos."""
    n = len(precios)
    if n < 3:
        return 0
    m = media(precios)
    if m <= 0:
        return 0
    umbral = m * umbral_pct / 100.0

    direcciones = []
    for i in range(1, n):
        d = precios[i] - precios[i - 1]
        if abs(d) >= umbral:
            direcciones.append(1 if d > 0 else -1)

    giros = 0
    for i in range(1, len(direcciones)):
        if direcciones[i] != direcciones[i - 1]:
            giros += 1
    return giros


def calcular_metricas(
    tiempos: Sequence,
    precios: Sequence,
    dias: int = 90,
    ahora: Optional[datetime] = None,
) -> Optional[dict]:
    """Empaqueta todas las métricas del filtro en un dict, o None si no hay
    puntos válidos en la ventana (producto sin histórico consultable)."""
    t, p = limpiar_serie(tiempos, precios, dias=dias, ahora=ahora)
    if not p:
        return None

    t_previo, p_previo, _, p_reciente = subserie_por_ventana(t, p, DIAS_RECIENTES_CAIDA)

    return {
        "span_dias": span_dias(t),
        "precio_actual": precio_actual(p),
        "minimo": minimo(p),
        "maximo": maximo(p),
        "media": media(p),
        "mediana_reciente": mediana(p_reciente) if p_reciente else None,
        "mediana_previa": mediana(p_previo) if p_previo else None,
        "cv_previa": coeficiente_variacion(p_previo) if len(p_previo) >= 2 else None,
        "tendencia_rel": pendiente_relativa(t, p),
        "giros": num_giros(p),
        "n_puntos": len(p),
    }
