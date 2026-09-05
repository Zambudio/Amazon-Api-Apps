"""
Comprueba la configuración inicial visible del Buscador de Chollos.

Estas pruebas protegen los valores que deben aparecer seleccionados al abrir
la ventana, sin necesitar levantar una interfaz gráfica durante pytest.
"""

import json

from src.ui.deals_gui import (
    CANTIDAD_PREDETERMINADA,
    DESCUENTO_MAXIMO_PREDETERMINADO,
    DESCUENTO_MINIMO_PREDETERMINADO,
    OPCION_TODAS,
    OPCIONES_CANTIDAD,
    productos_desde_json,
)


def test_filtros_predeterminados_del_buscador() -> None:
    """El buscador arranca con los filtros acordados para buscar chollos."""
    assert OPCION_TODAS == "Todas las categorías"
    assert DESCUENTO_MINIMO_PREDETERMINADO == "15"
    assert DESCUENTO_MAXIMO_PREDETERMINADO == "50"
    assert CANTIDAD_PREDETERMINADA == "Max"


def test_cantidad_predeterminada_existe_en_el_desplegable() -> None:
    """La selección inicial de cantidad debe ser una opción válida."""
    assert CANTIDAD_PREDETERMINADA in OPCIONES_CANTIDAD


def test_productos_desde_json_mapea_campos_del_barrido(tmp_path) -> None:
    """El JSON del barrido (scripts/test_busqueda_max_ofertas.py) se convierte
    en ProductInfo con los campos correctos para mostrarlos en la GUI."""
    json_path = tmp_path / "max_ofertas_test.json"
    json_path.write_text(json.dumps({
        "totales": {"ofertas_unicas": 2},
        "ofertas": [
            {
                "asin": "B0TEST11111",
                "titulo": "Auriculares Bluetooth",
                "marca": "Soundcore",
                "categoria": "Auriculares",
                "precio_actual": 24.99,
                "precio_anterior": 49.99,
                "descuento": 50,
                "valoracion": 4.5,
                "num_valoraciones": 1200,
                "url": "https://www.amazon.es/dp/B0TEST11111?tag=test",
                "imagen": "http://img.example/auriculares.jpg",
            },
            {
                "asin": "B0TEST22222",
                "titulo": "Sin imagen",
                "url": "",
                "imagen": "",
            },
        ],
    }), encoding="utf-8")

    chollos = productos_desde_json(str(json_path))

    assert len(chollos) == 2
    primero = chollos[0]
    assert primero.asin == "B0TEST11111"
    assert primero.titulo == "Auriculares Bluetooth"
    assert primero.marca == "Soundcore"
    assert primero.precio_actual == 24.99
    assert primero.precio_anterior == 49.99
    assert primero.descuento_porcentaje == 50
    assert primero.url_afiliado == "https://www.amazon.es/dp/B0TEST11111?tag=test"
    assert primero.imagen_principal == "http://img.example/auriculares.jpg"
    assert primero.moneda == "EUR"
    # Campos ausentes se rellenan con valores seguros.
    assert chollos[1].titulo == "Sin imagen"
    assert chollos[1].url_afiliado == ""
    assert chollos[1].imagen_principal == ""
