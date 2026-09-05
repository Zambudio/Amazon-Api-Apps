"""
Pruebas del caso de uso de filtrado por calidad (filter_chollos_calidad.py).
El filtro es SOLO por marcas (la API de Amazon no devuelve valoraciones, así
que el criterio de estrellas se descartó). Cubre el comportamiento por defecto
(solo marcas de calidad) y el de "desactivado" (solo_marcas_calidad=False).
"""

from src.use_cases.filter_chollos_calidad import FilterChollosCalidadUseCase
from src.domain.entities import ProductInfo


def _chollo(asin="B0TEST11111", marca="Sony"):
    return ProductInfo(
        asin=asin,
        titulo="Auriculares Bluetooth",
        marca=marca,
        descuento_porcentaje=40,
    )


def test_por_defecto_solo_deja_marcas_de_calidad() -> None:
    chollos = [
        _chollo("A", marca="Sony"),
        _chollo("B", marca="MarcaDesconocida"),
        _chollo("C", marca="Samsung"),
    ]
    resultado = FilterChollosCalidadUseCase().execute(chollos)

    assert [c.asin for c in resultado] == ["A", "C"]


def test_con_marca_vacia_se_descarta() -> None:
    chollos = [_chollo("A", marca="")]
    resultado = FilterChollosCalidadUseCase().execute(chollos)

    assert resultado == []


def test_sin_marca_no_descarta_por_marca() -> None:
    chollos = [
        _chollo("A", marca="MarcaDesconocida"),
        _chollo("B", marca="Sony"),
    ]
    resultado = FilterChollosCalidadUseCase().execute(
        chollos, {"solo_marcas_calidad": False}
    )

    assert [c.asin for c in resultado] == ["A", "B"]


def test_normaliza_marca_con_sufijo() -> None:
    chollos = [_chollo("A", marca="Sony Electronics")]
    resultado = FilterChollosCalidadUseCase().execute(chollos)

    assert [c.asin for c in resultado] == ["A"]


def test_lista_vacia_devuelve_vacia() -> None:
    assert FilterChollosCalidadUseCase().execute([]) == []
