"""
Pruebas de la lista de marcas de calidad (marcas_calidad.py).
Verifican la normalización de la marca que devuelve Amazon (mayúsculas,
sufijos legales/técnicos), el match por primera palabra (sub-marcas), el
mapa de marcas por categoría y que marcas genéricas o vacías se descartan.
"""

from src.domain.marcas_calidad import es_marca_calidad, marcas_para_categoria


def test_marcas_conocidas_son_de_calidad() -> None:
    assert es_marca_calidad("Sony")
    assert es_marca_calidad("SONY")
    assert es_marca_calidad("Samsung")
    assert es_marca_calidad("Apple")
    assert es_marca_calidad("Logitech")
    assert es_marca_calidad("Anker")
    assert es_marca_calidad("Bose")
    assert es_marca_calidad("Western Digital")
    # Marcas nuevas ampliadas (sondeo 2026-08-29)
    assert es_marca_calidad("Hisense")
    assert es_marca_calidad("Soundcore")
    assert es_marca_calidad("SteelSeries")
    assert es_marca_calidad("HyperX")
    assert es_marca_calidad("DJI")


def test_marcas_con_sufijos_se_normalizan() -> None:
    assert es_marca_calidad("Sony Corporation")
    assert es_marca_calidad("Sony Inc.")
    assert es_marca_calidad("Samsung Electronics")
    assert es_marca_calidad("Google LLC")
    assert es_marca_calidad("TP-Link")
    assert es_marca_calidad("  sony  ")
    assert es_marca_calidad("Samsung Corp.")
    assert es_marca_calidad("Western Digital Technologies, Inc.")


def test_submarcas_se_reconocen_por_primera_palabra() -> None:
    # Sub-marcas / variantes que Amazon a veces antepone al nombre madre.
    assert es_marca_calidad("Logitech G")
    assert es_marca_calidad("Soundcore by Anker")
    assert es_marca_calidad("Samsung EVO")
    assert es_marca_calidad("Asus ROG Strix")


def test_marcas_genericas_no_son_de_calidad() -> None:
    assert not es_marca_calidad("Generic")
    assert not es_marca_calidad("No-Name")
    assert not es_marca_calidad("Powerpack")
    assert not es_marca_calidad("TECHNOBRANDS")
    # Genéricas chinas que dominan los refinements y ensucian el barrido.
    assert not es_marca_calidad("BROTECT")
    assert not es_marca_calidad("MOKO")
    assert not es_marca_calidad("TESSAN")
    assert not es_marca_calidad("ZDK")
    assert not es_marca_calidad("CARPURIDE")
    assert not es_marca_calidad("BIRDCLAW")


def test_marca_vacia_no_es_de_calidad() -> None:
    assert not es_marca_calidad("")
    assert not es_marca_calidad(None)


def test_marcas_para_categoria_devuelve_candidatas_de_la_categoria() -> None:
    fotografia = marcas_para_categoria("Fotografía y videocámaras")
    assert "canon" in fotografia and "nikon" in fotografia and "dji" in fotografia
    # No incluye marcas de otras categorías (evita barridos irrelevantes).
    assert "gigaset" not in fotografia
    assert "canon" in marcas_para_categoria("Impresoras y consumibles")


def test_marcas_para_categoria_filtra_marcas_no_curdas() -> None:
    # Las candidatas del mapa se validan contra MARCAS_CALIDAD en runtime.
    marca_generica = "BROTECT"
    fotografia = marcas_para_categoria("Fotografía y videocámaras")
    assert marca_generica not in fotografia


def test_marcas_para_categoria_desconocida_devuelve_vacia() -> None:
    assert marcas_para_categoria("Categoría inexistente") == []
