"""
Pruebas del cliente de integración con Keepa (keepa_client.py).

Sustituye la librería `keepa` por un doble que registra las llamadas, para
verificar el chunking por lotes, la selección de la serie NEW/AMAZON y el
manejo de errores (devolver None + log) sin tocar la API de pago.
"""

from datetime import datetime

import keepa

from src.integrations.keepa.keepa_client import KeepaClient
from src.config.settings import Config


class FakeKeepaApi:
    """Doble de la librería keepa: devuelve un producto con serie NEW por ASIN."""

    def __init__(self, key, fallar=False, serie_datos=None):
        self.key = key
        self.fallar = fallar
        self.serie_datos = serie_datos
        self.llamadas = []

    def query(self, asins, **kwargs):
        self.llamadas.append((list(asins), kwargs))
        if self.fallar:
            raise RuntimeError("token agotado")
        return [self._producto(a) for a in asins]

    def _producto(self, asin):
        if self.serie_datos is not None:
            datos = self.serie_datos
        else:
            datos = {
                "NEW": [100.0],
                "NEW_time": [datetime(2026, 8, 1)],
            }
        return {"asin": asin, "data": datos}


def _cliente(api, api_key="clave-test"):
    return KeepaClient(api_key=api_key) if api_key else KeepaClient()


def test_consulta_en_lotes_y_pasa_dias_dominio(monkeypatch):
    api = FakeKeepaApi("clave-test")
    monkeypatch.setattr(keepa, "Keepa", lambda key: api)

    client = _cliente(api)
    asins = [f"B{i:09d}" for i in range(120)]
    resultado = client.obtener_historial(asins, dias=90)

    assert len(resultado) == 120
    # La librería limita a 100 por petición; nuestro chunk conservador es 50.
    tamanos = [len(c[0]) for c in api.llamadas]
    assert tamanos == [50, 50, 20]
    llamada = api.llamadas[0][1]
    assert llamada["domain"] == "es"
    assert llamada["days"] == 90
    assert llamada["history"] is True


def test_fallback_a_serie_amazon(monkeypatch):
    api = FakeKeepaApi("clave-test", serie_datos={"AMAZON": [80.0], "AMAZON_time": [datetime(2026, 8, 1)]})
    monkeypatch.setattr(keepa, "Keepa", lambda key: api)

    client = _cliente(api)
    resultado = client.obtener_historial(["B0TEST11111"])

    tiempo, precios = resultado["B0TEST11111"]
    assert list(precios) == [80.0]


def test_keepa_sin_serie_no_incluye_el_producto(monkeypatch):
    api = FakeKeepaApi("clave-test", serie_datos={})
    monkeypatch.setattr(keepa, "Keepa", lambda key: api)

    client = _cliente(api)
    assert client.obtener_historial(["B0TEST11111"]) == {}


def test_error_de_api_devuelve_none(monkeypatch):
    api = FakeKeepaApi("clave-test", fallar=True)
    monkeypatch.setattr(keepa, "Keepa", lambda key: api)

    client = _cliente(api)
    assert client.obtener_historial(["B0TEST11111"]) is None


def test_sin_clave_cliente_no_disponible(monkeypatch):
    monkeypatch.setattr(Config, "KEEPA_API_KEY", "")

    client = KeepaClient()
    assert not client.disponible
    assert client.obtener_historial(["B0TEST11111"]) is None
