"""
Pruebas del caso de uso Buscar Chollos por Categoría.
Valida el filtro por rango de descuento, el orden de resultados, la
paginación (pedir varias páginas a la API hasta agotar resultados) y el
barrido por marcas, sin llamar realmente a la API de Amazon.
"""

import itertools

import pytest

from src.use_cases import find_deals
from src.use_cases.find_deals import FindDealsUseCase
from src.domain.entities import ProductInfo

ITEMS = find_deals._API_ITEM_COUNT
MAX_PAGINAS = find_deals._API_MAX_PAGES
NUM_ESTRATEGIAS = len(find_deals._SORT_STRATEGIES)

# Generador de ASINs únicos para los productos de prueba: si dos productos
# compartieran ASIN, la deduplicación del caso de uso descartaría uno.
_contador_asin = itertools.count()


def _producto(titulo="Producto", descuento=None, imagen="http://img", asin=None, marca=None):
    return ProductInfo(
        asin=asin or f"B{next(_contador_asin):09d}",
        titulo=titulo,
        descuento_porcentaje=descuento,
        imagen_principal=imagen,
        marca=marca or "",
    )


class FakeAmazonService:
    """Simula el servicio de Amazon devolviendo páginas de productos.

    Recibe una lista de páginas (cada una, una lista de productos) para las
    búsquedas normales y registra todas las llamadas para poder comprobarlas
    en los tests. Las marcas (refinements) y las páginas por marca se
    configuran por test (marcas, _por_marca).
    """

    def __init__(self, paginas):
        self._paginas = paginas
        self._por_marca = {}
        self.llamadas = []
        self.marcas = []
        self.fallar_refinements = False
        self.llamadas_refinements = 0

    def search_deals(self, categoria, min_saving_percent, item_count, item_page=None, sort_by=None, brand=None):
        self.llamadas.append((categoria, min_saving_percent, item_count, item_page, sort_by, brand))
        if brand is not None:
            paginas = self._por_marca.get((categoria, brand), [])
        else:
            paginas = self._paginas
        indice = (item_page or 1) - 1
        if indice < len(paginas):
            return paginas[indice]
        return []

    def get_brand_refinements(self, categoria):
        self.llamadas_refinements += 1
        if self.fallar_refinements:
            raise RuntimeError("fallo de red en refinements")
        return self.marcas


@pytest.fixture(autouse=True)
def sin_pausas(monkeypatch):
    """Anula la pausa entre páginas para que los tests sean instantáneos."""
    monkeypatch.setattr(find_deals.time, "sleep", lambda segundos: None)


def test_execute_filtra_por_descuento_minimo_y_ordena_descendente() -> None:
    productos = [
        _producto("Bajo descuento", descuento=10),
        _producto("Descuento medio", descuento=30),
        _producto("Descuento alto", descuento=50),
        _producto("Sin descuento", descuento=None),
    ]
    fake_service = FakeAmazonService([productos])
    use_case = FindDealsUseCase(amazon_service=fake_service)

    resultado = use_case.execute("Videojuegos", min_descuento=20, limite=10)

    assert [p.titulo for p in resultado] == ["Descuento alto", "Descuento medio"]
    # A la API se le pide el descuento real (20), no 1; el filtro local se
    # mantiene como red de seguridad. La primera llamada es la página 1 del
    # primer SortBy (Featured, sin marca).
    assert fake_service.llamadas[0] == ("Videojuegos", 20, ITEMS, 1, None, None)


def test_execute_pide_a_la_api_el_umbral_configurado() -> None:
    productos = [_producto("Marca en oferta", descuento=25, marca="Sony")]
    fake_service = FakeAmazonService([productos])
    use_case = FindDealsUseCase(amazon_service=fake_service)

    use_case.execute("Videojuegos", min_descuento=15, limite=10)

    # min_saving_percent en la petición = 15 (min_descuento), no 1.
    assert all(ll[1] == 15 for ll in fake_service.llamadas if ll[5] is None)


def test_execute_puede_sobrescribir_el_umbral_de_api() -> None:
    productos = [_producto("Marca en oferta", descuento=25, marca="Sony")]
    fake_service = FakeAmazonService([productos])
    use_case = FindDealsUseCase(amazon_service=fake_service)

    use_case.execute(
        "Videojuegos",
        min_descuento=15,
        limite=10,
        min_saving_percent_api=30,
    )

    assert all(ll[1] == 30 for ll in fake_service.llamadas if ll[5] is None)


def test_execute_descarta_productos_sin_titulo_o_imagen() -> None:
    productos = [
        _producto("Con todo", descuento=30, imagen="http://img"),
        _producto("Sin imagen", descuento=30, imagen=""),
        ProductInfo(asin="B111111111", titulo="", descuento_porcentaje=30, imagen_principal="http://img"),
    ]
    fake_service = FakeAmazonService([productos])
    use_case = FindDealsUseCase(amazon_service=fake_service)

    resultado = use_case.execute("Videojuegos", min_descuento=20, limite=10)

    assert [p.titulo for p in resultado] == ["Con todo"]


def test_execute_respeta_el_limite() -> None:
    productos = [_producto(f"Producto {i}", descuento=20 + i) for i in range(5)]
    fake_service = FakeAmazonService([productos])
    use_case = FindDealsUseCase(amazon_service=fake_service)

    resultado = use_case.execute("Videojuegos", min_descuento=20, limite=2)

    assert len(resultado) == 2
    assert resultado[0].titulo == "Producto 4"


def test_execute_filtra_por_descuento_maximo() -> None:
    productos = [
        _producto("Descuento bajo", descuento=20),
        _producto("Descuento medio", descuento=40),
        _producto("Descuento muy alto", descuento=80),
    ]
    fake_service = FakeAmazonService([productos])
    use_case = FindDealsUseCase(amazon_service=fake_service)

    resultado = use_case.execute("Videojuegos", min_descuento=10, max_descuento=50, limite=10)

    assert [p.titulo for p in resultado] == ["Descuento medio", "Descuento bajo"]


def test_execute_sin_descuento_maximo_no_filtra() -> None:
    productos = [
        _producto("Descuento medio", descuento=40),
        _producto("Descuento muy alto", descuento=80),
    ]
    fake_service = FakeAmazonService([productos])
    use_case = FindDealsUseCase(amazon_service=fake_service)

    resultado = use_case.execute("Videojuegos", min_descuento=10, max_descuento=None, limite=10)

    assert [p.titulo for p in resultado] == ["Descuento muy alto", "Descuento medio"]


def test_execute_pide_paginas_hasta_agotar_resultados() -> None:
    # 3 páginas completas: el bucle sigue hasta que llega una página vacía
    # (la 4ª), y no se corta antes aunque haya suficiente con el límite.
    paginas = [
        [_producto(f"P{p}-{i}", descuento=30 if i < 5 else 5) for i in range(ITEMS)]
        for p in range(3)
    ]
    fake_service = FakeAmazonService(paginas)
    use_case = FindDealsUseCase(amazon_service=fake_service)

    resultado = use_case.execute("Videojuegos", min_descuento=20, limite=15)

    assert len(resultado) == 15
    # La primera estrategia pide páginas 1, 2, 3 y corta en la 4ª (vacía).
    assert [ll[3] for ll in fake_service.llamadas[:4]] == [1, 2, 3, 4]


def test_execute_para_en_pagina_vacia() -> None:
    # Una página corta (menos de 10 productos) NO es la última: Amazon a veces
    # devuelve páginas cortas y aun así hay más. Solo se deja de pedir cuando
    # llega una página completamente vacía.
    paginas = [
        [_producto(f"P1-{i}", descuento=30) for i in range(3)],
        [_producto(f"P2-{i}", descuento=30) for i in range(5)],
        [],
    ]
    fake_service = FakeAmazonService(paginas)
    use_case = FindDealsUseCase(amazon_service=fake_service)

    resultado = use_case.execute("Videojuegos", min_descuento=20, limite=50)

    assert len(resultado) == 8
    assert [ll[3] for ll in fake_service.llamadas[:3]] == [1, 2, 3]


def test_execute_nunca_pide_mas_de_diez_paginas_por_estrategia() -> None:
    # Todas las páginas vienen llenas pero ningún producto supera el filtro:
    # el bucle debe parar en la página 10 (límite de la API).
    paginas = [
        [_producto(f"P{p}-{i}", descuento=5) for i in range(ITEMS)]
        for p in range(20)
    ]
    fake_service = FakeAmazonService(paginas)
    use_case = FindDealsUseCase(amazon_service=fake_service)

    resultado = use_case.execute("Videojuegos", min_descuento=20, limite=50, incluir_marcas=False)

    assert resultado == []
    assert len(fake_service.llamadas) == NUM_ESTRATEGIAS * MAX_PAGINAS


def test_execute_deduplica_asins_repetidos_entre_paginas() -> None:
    repetido = _producto("Repetido", descuento=40, asin="B999999999")
    paginas = [
        [repetido] + [_producto(f"P1-{i}", descuento=30) for i in range(ITEMS - 1)],
        [repetido] + [_producto(f"P2-{i}", descuento=30) for i in range(ITEMS - 1)],
    ]
    fake_service = FakeAmazonService(paginas)
    use_case = FindDealsUseCase(amazon_service=fake_service)

    resultado = use_case.execute("Videojuegos", min_descuento=20, limite=50)

    asins = [p.asin for p in resultado]
    assert asins.count("B999999999") == 1


def test_execute_sin_limite_devuelve_todo_lo_encontrado() -> None:
    # Con limite=None se recorren todas las páginas disponibles y se
    # devuelve todo lo que supere el filtro, sin recortar.
    paginas = [
        [_producto(f"P{p}-{i}", descuento=30) for i in range(ITEMS)]
        for p in range(4)
    ]
    fake_service = FakeAmazonService(paginas)
    use_case = FindDealsUseCase(amazon_service=fake_service)

    resultado = use_case.execute("Videojuegos", min_descuento=20, limite=None)

    # 4 páginas llenas + la 5ª vacía que marca el final.
    assert len(resultado) == 4 * ITEMS
    assert [ll[3] for ll in fake_service.llamadas[:5]] == [1, 2, 3, 4, 5]


def test_execute_conserva_resultados_parciales_si_una_pagina_falla() -> None:
    class ServicioQueFallaEnPagina2(FakeAmazonService):
        def search_deals(self, categoria, min_saving_percent, item_count, item_page=None, sort_by=None, brand=None):
            if item_page == 2 and brand is None:
                raise RuntimeError("fallo de red")
            return super().search_deals(categoria, min_saving_percent, item_count, item_page, sort_by, brand)

    paginas = [[_producto(f"P{i}", descuento=30) for i in range(ITEMS)]]
    fake_service = ServicioQueFallaEnPagina2(paginas)
    use_case = FindDealsUseCase(amazon_service=fake_service)

    resultado = use_case.execute("Videojuegos", min_descuento=20, limite=50)

    # La página 1 se conserva aunque la 2 haya fallado.
    assert len(resultado) == ITEMS


def test_execute_barrido_por_marcas_anade_productos_unicos(monkeypatch) -> None:
    # El barrido usa el mapa de marcas de calidad por categoría (y las marcas
    # de calidad de los refinements). Para aislar el test, fijamos el mapa.
    monkeypatch.setattr(
        find_deals, "marcas_para_categoria", lambda categoria: ["Xiaomi", "Samsung"]
    )
    paginas = [[_producto(f"P{i}", descuento=30) for i in range(2)]]
    fake_service = FakeAmazonService(paginas)
    fake_service.marcas = []
    fake_service._por_marca = {
        ("Videojuegos", "Xiaomi"): [[_producto("Marca Xiaomi", descuento=35)]],
        ("Videojuegos", "Samsung"): [[_producto("Marca Samsung", descuento=45)]],
    }
    use_case = FindDealsUseCase(amazon_service=fake_service)

    resultado = use_case.execute("Videojuegos", min_descuento=20, limite=50)

    titulos = {p.titulo for p in resultado}
    assert {"Marca Xiaomi", "Marca Samsung"} <= titulos
    # Cada marca se busca hasta que una página llega vacía (aquí: pág. 1 llena
    # y pág. 2 vacía), así que hay 2 llamadas por marca.
    marcas_pedidas = [ll[5] for ll in fake_service.llamadas if ll[5] is not None]
    assert set(marcas_pedidas) == {"Xiaomi", "Samsung"}


def test_execute_barrido_por_marcas_deduplica(monkeypatch) -> None:
    monkeypatch.setattr(
        find_deals, "marcas_para_categoria", lambda categoria: ["Xiaomi"]
    )
    repetido = _producto("Aparece en el sort y en la marca", descuento=40, asin="B777777777")
    fake_service = FakeAmazonService([[repetido]])
    fake_service.marcas = []
    fake_service._por_marca = {("Videojuegos", "Xiaomi"): [[repetido]]}
    use_case = FindDealsUseCase(amazon_service=fake_service)

    resultado = use_case.execute("Videojuegos", min_descuento=20, limite=50)

    assert [p.asin for p in resultado].count("B777777777") == 1


def test_execute_sin_marcas_no_hace_barrido() -> None:
    fake_service = FakeAmazonService([[_producto("P0", descuento=30)]])
    fake_service.marcas = ["Xiaomi"]
    use_case = FindDealsUseCase(amazon_service=fake_service)

    resultado = use_case.execute("Videojuegos", min_descuento=20, limite=10, incluir_marcas=False)

    assert [p.titulo for p in resultado] == ["P0"]
    assert fake_service.llamadas_refinements == 0
    assert all(ll[5] is None for ll in fake_service.llamadas)


def test_execute_sin_refinements_no_rompe() -> None:
    fake_service = FakeAmazonService([[_producto("P0", descuento=30)]])
    use_case = FindDealsUseCase(amazon_service=fake_service)

    resultado = use_case.execute("Videojuegos", min_descuento=20, limite=10)

    assert [p.titulo for p in resultado] == ["P0"]


def test_execute_si_refinements_fallan_conserva_resultados() -> None:
    fake_service = FakeAmazonService([[_producto("P0", descuento=30)]])
    fake_service.fallar_refinements = True
    use_case = FindDealsUseCase(amazon_service=fake_service)

    resultado = use_case.execute("Videojuegos", min_descuento=20, limite=10)

    assert [p.titulo for p in resultado] == ["P0"]


def test_execute_barrido_respeta_max_marcas_y_paginas(monkeypatch) -> None:
    monkeypatch.setattr(
        find_deals, "marcas_para_categoria", lambda categoria: ["A", "B", "C"]
    )
    fake_service = FakeAmazonService([])
    fake_service.marcas = []
    fake_service._por_marca = {
        ("Videojuegos", marca): [
            [_producto(f"{marca} p1-{i}", descuento=30) for i in range(ITEMS)],
            [_producto(f"{marca} p2-{i}", descuento=30) for i in range(ITEMS)],
        ]
        for marca in ("A", "B", "C")
    }
    use_case = FindDealsUseCase(amazon_service=fake_service)

    use_case.execute("Videojuegos", min_descuento=20, limite=50, max_marcas=2, paginas_por_marca=2)

    con_marca = [ll for ll in fake_service.llamadas if ll[5] is not None]
    assert [ll[5] for ll in con_marca] == ["A", "A", "B", "B"]
    assert [ll[3] for ll in con_marca] == [1, 2, 1, 2]


def test_execute_barrido_ignora_marcas_genericas_de_refinements(monkeypatch) -> None:
    # El mapa no tiene marcas para esta categoría y los refinements devuelven
    # marcas genéricas chinas: el barrido NO debe usar ninguna de ellas.
    monkeypatch.setattr(find_deals, "marcas_para_categoria", lambda categoria: [])
    fake_service = FakeAmazonService([[_producto("P0", descuento=30)]])
    fake_service.marcas = ["BROTECT", "MOKO"]
    fake_service._por_marca = {
        ("Videojuegos", "BROTECT"): [[_producto("Genérica", descuento=50)]],
        ("Videojuegos", "MOKO"): [[_producto("Genérica 2", descuento=60)]],
    }
    use_case = FindDealsUseCase(amazon_service=fake_service)

    resultado = use_case.execute("Videojuegos", min_descuento=20, limite=50)

    assert [p.titulo for p in resultado] == ["P0"]
    assert all(ll[5] is None for ll in fake_service.llamadas)


def test_execute_barrido_anade_marcas_de_quality_de_refinements(monkeypatch) -> None:
    # Marcas que no están en el mapa pero sí son de calidad según los
    # refinements: se añaden al barrido (no se pierden).
    monkeypatch.setattr(find_deals, "marcas_para_categoria", lambda categoria: [])
    fake_service = FakeAmazonService([[_producto("P0", descuento=30)]])
    fake_service.marcas = ["SONY"]
    fake_service._por_marca = {
        ("Videojuegos", "SONY"): [[_producto("Sony extra", descuento=45)]],
    }
    use_case = FindDealsUseCase(amazon_service=fake_service)

    resultado = use_case.execute("Videojuegos", min_descuento=20, limite=50)

    assert {p.titulo for p in resultado} == {"P0", "Sony extra"}


def test_execute_prioriza_marcas_de_calidad_en_el_orden() -> None:
    # Aunque el genérico tenga más descuento, las marcas de calidad van delante.
    productos = [
        _producto("Marca genérica 50%", descuento=50, marca="BROTECT"),
        _producto("Sony 30%", descuento=30, marca="Sony"),
        _producto("Samsung 40%", descuento=40, marca="Samsung Corp."),
    ]
    fake_service = FakeAmazonService([productos])
    use_case = FindDealsUseCase(amazon_service=fake_service)

    resultado = use_case.execute("Videojuegos", min_descuento=20, limite=10)

    assert [p.titulo for p in resultado] == [
        "Samsung 40%", "Sony 30%", "Marca genérica 50%",
    ]


def test_execute_sin_priorizar_marcas_mantiene_orden_por_descuento() -> None:
    productos = [
        _producto("Marca genérica 50%", descuento=50, marca="BROTECT"),
        _producto("Sony 30%", descuento=30, marca="Sony"),
    ]
    fake_service = FakeAmazonService([productos])
    use_case = FindDealsUseCase(amazon_service=fake_service)

    resultado = use_case.execute(
        "Videojuegos", min_descuento=20, limite=10, priorizar_marcas=False
    )

    assert [p.titulo for p in resultado] == ["Marca genérica 50%", "Sony 30%"]


def test_execute_todas_sin_limite_devuelve_todo() -> None:
    paginas_por_categoria = {
        "Videojuegos": [[_producto(f"J{i}", descuento=30) for i in range(3)]],
        "Electrónica": [[_producto(f"E{i}", descuento=40) for i in range(4)]],
    }
    fake_service = FakeAmazonServicePorCategoria(paginas_por_categoria)
    use_case = FindDealsUseCase(amazon_service=fake_service)

    resultado = use_case.execute_todas(
        ["Videojuegos", "Electrónica"], min_descuento=20, limite=None
    )

    assert len(resultado) == 7


class FakeAmazonServicePorCategoria(FakeAmazonService):
    """Fake que devuelve productos distintos según la categoría pedida."""

    def __init__(self, paginas_por_categoria):
        super().__init__(paginas=[])
        self._por_categoria = paginas_por_categoria

    def search_deals(self, categoria, min_saving_percent, item_count, item_page=None, sort_by=None, brand=None):
        self.llamadas.append((categoria, min_saving_percent, item_count, item_page, sort_by, brand))
        if brand is not None:
            paginas = self._por_marca.get((categoria, brand), [])
        else:
            paginas = self._por_categoria.get(categoria, [])
        indice = (item_page or 1) - 1
        if indice < len(paginas):
            return paginas[indice]
        return []


def test_execute_todas_junta_categorias_y_devuelve_los_mejores() -> None:
    paginas_por_categoria = {
        "Videojuegos": [[_producto("Juego", descuento=30)]],
        "Electrónica": [[_producto("Tele", descuento=70), _producto("Cable", descuento=25)]],
    }
    fake_service = FakeAmazonServicePorCategoria(paginas_por_categoria)
    use_case = FindDealsUseCase(amazon_service=fake_service)

    resultado = use_case.execute_todas(
        ["Videojuegos", "Electrónica"], min_descuento=20, limite=2
    )

    # De los 3 chollos totales se quedan los 2 mejores, ordenados por descuento.
    assert [p.titulo for p in resultado] == ["Tele", "Juego"]
    categorias_pedidas = {ll[0] for ll in fake_service.llamadas}
    assert categorias_pedidas == {"Videojuegos", "Electrónica"}


def test_execute_todas_deduplica_asins_entre_categorias() -> None:
    repetido = _producto("En dos categorías", descuento=40, asin="B888888888")
    paginas_por_categoria = {
        "Videojuegos": [[repetido]],
        "Electrónica": [[repetido, _producto("Solo aquí", descuento=30)]],
    }
    fake_service = FakeAmazonServicePorCategoria(paginas_por_categoria)
    use_case = FindDealsUseCase(amazon_service=fake_service)

    resultado = use_case.execute_todas(
        ["Videojuegos", "Electrónica"], min_descuento=20, limite=10
    )

    assert [p.asin for p in resultado].count("B888888888") == 1
    assert len(resultado) == 2


def test_execute_todas_avisa_del_progreso() -> None:
    paginas_por_categoria = {"Videojuegos": [], "Electrónica": []}
    fake_service = FakeAmazonServicePorCategoria(paginas_por_categoria)
    use_case = FindDealsUseCase(amazon_service=fake_service)
    avisos = []

    use_case.execute_todas(
        ["Videojuegos", "Electrónica"],
        min_descuento=20,
        limite=10,
        on_progress=lambda msg: avisos.append(msg),
    )

    assert avisos[0] == "Categoría 1/2: Videojuegos"
    assert avisos[1].startswith("Buscando en 'Videojuegos'")
    assert "Categoría 2/2: Electrónica" in avisos


def test_execute_todas_sin_marcas_no_hace_barrido() -> None:
    paginas_por_categoria = {
        "Videojuegos": [[_producto("Juego", descuento=30)]],
        "Electrónica": [[_producto("Tele", descuento=40)]],
    }
    fake_service = FakeAmazonServicePorCategoria(paginas_por_categoria)
    fake_service.marcas = ["Xiaomi"]
    use_case = FindDealsUseCase(amazon_service=fake_service)

    resultado = use_case.execute_todas(
        ["Videojuegos", "Electrónica"],
        min_descuento=20,
        limite=10,
        incluir_marcas=False,
    )

    assert len(resultado) == 2
    assert fake_service.llamadas_refinements == 0
