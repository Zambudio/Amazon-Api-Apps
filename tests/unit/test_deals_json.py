"""
Pruebas del almacenamiento de ofertas en JSON (deals_json.py).
Verifica que el formato guardado por guardar_ofertas_json puede leerse con
productos_desde_json (round-trip) y que se respeta el formato estándar.
"""

import json

from src.integrations.storage.deals_json import guardar_ofertas_json, productos_desde_json
from src.domain.entities import ProductInfo


def _producto(asin="B0TEST11111"):
    return ProductInfo(
        asin=asin,
        titulo="Auriculares Bluetooth",
        marca="Soundcore",
        categoria="Auriculares",
        precio_actual=24.99,
        precio_anterior=49.99,
        descuento_porcentaje=50,
        valoracion=4.5,
        num_valoraciones=1200,
        url_afiliado="https://www.amazon.es/dp/B0TEST11111?tag=test",
        imagen_principal="http://img.example/auriculares.jpg",
    )


def test_round_trip_guarda_y_lee_ofertas(tmp_path) -> None:
    ruta = str(tmp_path / "max_ofertas_test.json")
    chollos = [_producto(), _producto(asin="B0TEST22222")]

    guardar_ofertas_json(chollos, ruta, metadatos={"min_descuento": 15})

    leidos = productos_desde_json(ruta)
    assert len(leidos) == 2

    primero = leidos[0]
    assert primero.asin == "B0TEST11111"
    assert primero.titulo == "Auriculares Bluetooth"
    assert primero.marca == "Soundcore"
    assert primero.precio_actual == 24.99
    assert primero.precio_anterior == 49.99
    assert primero.descuento_porcentaje == 50
    assert primero.url_afiliado == "https://www.amazon.es/dp/B0TEST11111?tag=test"
    assert primero.imagen_principal == "http://img.example/auriculares.jpg"
    assert primero.moneda == "EUR"

    # Los metadatos se conservan en la raíz del JSON (contexto del barrido).
    with open(ruta, encoding="utf-8") as f:
        data = json.load(f)
    assert data["min_descuento"] == 15
    assert data["timestamp"]
    assert len(data["ofertas"]) == 2


def test_guardar_ofertas_json_crea_el_directorio(tmp_path) -> None:
    ruta = str(tmp_path / "subcarpeta" / "max_ofertas_test.json")

    guardar_ofertas_json([_producto()], ruta)

    assert (tmp_path / "subcarpeta" / "max_ofertas_test.json").exists()


def test_productos_desde_json_sin_ofertas_devuelve_vacio(tmp_path) -> None:
    ruta = tmp_path / "max_ofertas_vacio.json"
    ruta.write_text(json.dumps({"totales": {"ofertas_unicas": 0}}), encoding="utf-8")

    assert productos_desde_json(str(ruta)) == []
