"""
Pruebas del caso de uso de filtrado por Keepa (filter_deals_keepa.py).

Usa un repositorio falso (sin tocar la API de pago) con series sintéticas que
reproducen los casos reales y engañosos: mínimo real, caída desde estable,
tendencia descendente, "sonda" (oscila sin salir de rango) y bajada desde un
precio inflado con precios mucho menores previos.
"""

from datetime import datetime, timedelta

from src.use_cases.filter_deals_keepa import FilterDealsKeepaUseCase
from src.domain.entities import ProductInfo


def _serie(precios, ahora=None):
    """Serie diaria de precios terminando hoy (o en `ahora`)."""
    ahora = ahora or datetime.now()
    inicio = ahora - timedelta(days=len(precios))
    return [inicio + timedelta(days=i) for i in range(len(precios))], [float(p) for p in precios]


def _chollo(asin="B0TEST11111"):
    return ProductInfo(
        asin=asin,
        titulo="Auriculares Bluetooth",
        descuento_porcentaje=50,
        precio_actual=24.99,
        precio_anterior=49.99,
    )


class FakeKeepaRepository:
    """Repositorio falso: devuelve las series que se le configuran por ASIN."""

    def __init__(self, series=None, fallar=False):
        self._series = series or {}
        self.fallar = fallar

    def obtener_historial(self, asins, dias=90):
        if self.fallar:
            return None
        return {a: self._series[a] for a in asins if a in self._series}


def test_minimo_real_pasa() -> None:
    """Estable 100 y el último día baja a 50: el precio está en el mínimo."""
    repo = FakeKeepaRepository({"A": _serie([100.0] * 89 + [50.0])})
    resultado = FilterDealsKeepaUseCase(repo).execute([_chollo("A")])
    assert [c.asin for c in resultado] == ["A"]


def test_caida_desde_estable_pasa() -> None:
    """80 días a 100 y 10 a 80: caída reciente desde un nivel estable."""
    repo = FakeKeepaRepository({"A": _serie([100.0] * 80 + [80.0] * 10)})
    resultado = FilterDealsKeepaUseCase(repo).execute([_chollo("A")])
    assert [c.asin for c in resultado] == ["A"]


def test_tendencia_descendente_pasa() -> None:
    """Descenso progresivo de 100 a 70 sin subidas: pendiente clara."""
    repo = FakeKeepaRepository({"A": _serie([100.0 - 0.5 * i for i in range(60)])})
    resultado = FilterDealsKeepaUseCase(repo).execute([_chollo("A")])
    assert [c.asin for c in resultado] == ["A"]


def test_sonda_oscilante_se_descarta() -> None:
    """Sube y baja constantemente sin salir del rango: gráfica señuelo."""
    repo = FakeKeepaRepository({"A": _serie([90.0, 110.0, 90.0, 110.0, 90.0, 110.0] * 15)})
    resultado = FilterDealsKeepaUseCase(repo).execute([_chollo("A")])
    assert resultado == []


def test_bajada_desde_precio_inflado_se_descarta() -> None:
    """Estuvo a 60 y ahora está a 85 (más de 20% por encima del mínimo): no es un mínimo real."""
    repo = FakeKeepaRepository({"A": _serie([60.0] * 60 + [85.0] * 30)})
    resultado = FilterDealsKeepaUseCase(repo).execute([_chollo("A")])
    assert resultado == []


def test_poca_historia_se_descarta() -> None:
    """Menos de la mitad de la ventana pedida: sin base para juzgar la gráfica."""
    repo = FakeKeepaRepository({"A": _serie([50.0] * 10)})
    resultado = FilterDealsKeepaUseCase(repo).execute([_chollo("A")])
    assert resultado == []


def test_sin_historial_se_descarta_solo_ese_producto() -> None:
    """El que no tiene histórico de Keepa se descarta; los demás se evalúan."""
    repo = FakeKeepaRepository({"A": _serie([100.0] * 89 + [50.0])})
    resultado = FilterDealsKeepaUseCase(repo).execute([_chollo("A"), _chollo("B")])
    assert [c.asin for c in resultado] == ["A"]


def test_keepa_sin_datos_devuelve_lista_sin_filtrar() -> None:
    """Sin API key o fallo total de la consulta, no se rompe el flujo."""
    repo = FakeKeepaRepository(fallar=True)
    chollos = [_chollo("A"), _chollo("B")]
    resultado = FilterDealsKeepaUseCase(repo).execute(chollos)
    assert resultado == chollos


def test_sin_config_funciona_con_umbrales_por_defecto() -> None:
    repo = FakeKeepaRepository({"A": _serie([100.0] * 89 + [50.0])})
    resultado = FilterDealsKeepaUseCase(repo).execute([_chollo("A")])
    assert [c.asin for c in resultado] == ["A"]


def test_config_filtra_por_ahorro_vs_media() -> None:
    """Con ahorro_vs_media muy exigente, un precio a 80 sobre media 99 se descarta."""
    repo = FakeKeepaRepository({"A": _serie([100.0] * 80 + [80.0] * 10)})
    resultado = FilterDealsKeepaUseCase(repo).execute([_chollo("A")], {"ahorro_vs_media": 30})
    # Media ≈ 98, precio 80 → ahorro 18% < 30% → no pasa.
    assert resultado == []
