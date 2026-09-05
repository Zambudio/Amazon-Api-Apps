"""
Pruebas de las métricas puras de serie de precios (keepa_metrics.py).
Cubren la limpieza de la serie (NaN/sin stock), las estadísticas básicas y los
detectores de "forma de gráfica": tendencia (pendiente) y oscilación (giros).
"""

from datetime import datetime, timedelta

import pytest

from src.domain.keepa_metrics import (
    limpiar_serie,
    span_dias,
    precio_actual,
    minimo,
    media,
    mediana,
    coeficiente_variacion,
    subserie_por_ventana,
    pendiente_relativa,
    num_giros,
    calcular_metricas,
    DIAS_RECIENTES_CAIDA,
)


def _serie(precios, dias=90, ahora=None):
    """Serie diaria de `dias` días terminando hoy (o en `ahora`)."""
    ahora = ahora or datetime.now()
    inicio = ahora - timedelta(days=len(precios))
    tiempos = [inicio + timedelta(days=i) for i in range(len(precios))]
    return tiempos, [float(p) for p in precios]


# ── Limpieza ──────────────────────────────────────────────────────────────

def test_limpiar_serie_descarta_sin_stock_y_fuera_de_ventana():
    t, p = _serie([100.0, -1.0, 90.0, float("nan"), 80.0])
    limpios, limpio_p = limpiar_serie(t, p, dias=90)
    assert limpio_p == [100.0, 90.0, 80.0]
    assert len(limpios) == 3


def test_limpiar_serie_respeta_la_ventana_de_dias():
    ahora = datetime.now()
    t, p = _serie([10.0] * 200, ahora=ahora)
    _, limpio_p = limpiar_serie(t, p, dias=30, ahora=ahora)
    # La ventana de 30 días deja 30 puntos (el primero cae justo en el borde).
    assert len(limpio_p) == 30


def test_limpiar_serie_vacia_sin_datos_validos():
    t, p = _serie([-1.0, float("nan"), 0.0])
    assert limpiar_serie(t, p, dias=90) == ([], [])


# ── Estadísticas básicas ──────────────────────────────────────────────────

def test_span_dias():
    t, p = _serie([1.0] * 60)
    assert span_dias(t) == pytest.approx(59.0)


def test_precio_actual_minimo_y_media():
    p = [10.0, 20.0, 30.0]
    assert precio_actual(p) == 30.0
    assert minimo(p) == 10.0
    assert media(p) == 20.0


def test_mediana_par_e_impar():
    assert mediana([1.0, 2.0, 3.0]) == 2.0
    assert mediana([1.0, 2.0, 3.0, 4.0]) == 2.5


def test_coeficiente_variacion_estabilidad():
    assert coeficiente_variacion([100.0] * 10) == 0.0
    # Población [100, 110]: media 105, std 5 → CV = 5/105 ≈ 0.0476.
    assert coeficiente_variacion([100.0, 110.0]) == pytest.approx(5.0 / 105.0)


# ── Ventana reciente ──────────────────────────────────────────────────────

def test_subserie_por_ventana_separa_previa_y_reciente():
    # La caída (últimos 8 puntos, 2.0) queda dentro de la ventana reciente de 7 días.
    t, p = _serie([5.0] * 82 + [2.0] * 8)
    previa_t, previa_p, reciente_t, reciente_p = subserie_por_ventana(t, p, DIAS_RECIENTES_CAIDA)
    assert all(x == 5.0 for x in previa_p)
    assert all(x == 2.0 for x in reciente_p)
    assert previa_p and reciente_p


# ── Tendencia (pendiente) ─────────────────────────────────────────────────

def test_pendiente_relativa_descendente_negativa():
    t, p = _serie([float(100 - i) for i in range(50)])
    assert pendiente_relativa(t, p) < 0


def test_pendiente_relativa_estable_cercana_a_cero():
    t, p = _serie([100.0] * 50)
    assert pendiente_relativa(t, p) == pytest.approx(0.0, abs=0.001)


# ── Oscilación (giros / sonda) ────────────────────────────────────────────

def test_num_giros_serie_monotona_es_cero():
    p = list(range(1, 30))
    assert num_giros(p) == 0


def test_num_giros_sonda_alta_oscilacion():
    p = [90.0, 110.0, 90.0, 110.0, 90.0, 110.0] * 10
    assert num_giros(p) > 20


def test_num_giros_ignora_ruido_pequeno():
    p = [100.0 + (0.01 if i % 2 else -0.01) for i in range(30)]
    assert num_giros(p) == 0


# ── calcular_metricas ─────────────────────────────────────────────────────

def test_calcular_metricas_completo():
    # La caída (8 últimos puntos a 50) queda dentro de la ventana reciente.
    ahora = datetime.now()
    t, p = _serie([100.0] * 82 + [50.0] * 8, ahora=ahora)
    m = calcular_metricas(t, p, dias=90, ahora=ahora)
    assert m is not None
    assert m["precio_actual"] == 50.0
    assert m["minimo"] == 50.0
    assert m["mediana_reciente"] == 50.0
    assert m["mediana_previa"] == 100.0
    assert m["cv_previa"] == pytest.approx(0.0, abs=0.001)
    assert m["span_dias"] == pytest.approx(89.0)


def test_calcular_metricas_sin_datos_devuelve_none():
    t, p = _serie([-1.0] * 30)
    assert calcular_metricas(t, p, dias=90) is None
