"""
Pruebas del caso de uso Buscar Chollos por Categoría.
Valida que el filtro de seguridad por descuento mínimo y el orden de
resultados funcionen, sin llamar realmente a la API de Amazon.
"""

from src.use_cases.find_deals import FindDealsUseCase
from src.domain.entities import ProductInfo


def _producto(titulo="Producto", descuento=None, imagen="http://img", asin=None):
    import uuid
    return ProductInfo(
        asin=asin or str(uuid.uuid4())[:10],
        titulo=titulo,
        descuento_porcentaje=descuento,
        imagen_principal=imagen,
    )


class FakeAmazonService:
    def __init__(self, productos):
        self._productos = productos
        self.llamadas = []

    def search_deals(self, categoria, min_saving_percent, item_count, item_page=1):
        self.llamadas.append((categoria, min_saving_percent, item_count, item_page))
        # Return products only on the first page to simulate end of results
        return self._productos if item_page == 1 else []


def test_execute_filtra_por_descuento_minimo_y_ordena_descendente() -> None:
    productos = [
        _producto("Bajo descuento", descuento=10),
        _producto("Descuento medio", descuento=30),
        _producto("Descuento alto", descuento=50),
        _producto("Sin descuento", descuento=None),
    ]
    fake_service = FakeAmazonService(productos)
    use_case = FindDealsUseCase(amazon_service=fake_service)

    resultado = use_case.execute("Videojuegos", min_descuento=20, limite=10)

    assert [p.titulo for p in resultado] == ["Descuento alto", "Descuento medio"]
    assert ("Videojuegos", 1, 100, 1) in fake_service.llamadas


def test_execute_descarta_productos_sin_titulo_o_imagen() -> None:
    productos = [
        _producto("Con todo", descuento=30, imagen="http://img"),
        _producto("Sin imagen", descuento=30, imagen=""),
        ProductInfo(asin="B111111111", titulo="", descuento_porcentaje=30, imagen_principal="http://img"),
    ]
    fake_service = FakeAmazonService(productos)
    use_case = FindDealsUseCase(amazon_service=fake_service)

    resultado = use_case.execute("Videojuegos", min_descuento=20, limite=10)

    assert [p.titulo for p in resultado] == ["Con todo"]


def test_execute_respeta_el_limite() -> None:
    productos = [_producto(f"Producto {i}", descuento=20 + i) for i in range(5)]
    fake_service = FakeAmazonService(productos)
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
    fake_service = FakeAmazonService(productos)
    use_case = FindDealsUseCase(amazon_service=fake_service)

    resultado = use_case.execute("Videojuegos", min_descuento=10, max_descuento=50, limite=10)

    assert [p.titulo for p in resultado] == ["Descuento medio", "Descuento bajo"]


def test_execute_sin_descuento_maximo_no_filtra() -> None:
    productos = [
        _producto("Descuento medio", descuento=40),
        _producto("Descuento muy alto", descuento=80),
    ]
    fake_service = FakeAmazonService(productos)
    use_case = FindDealsUseCase(amazon_service=fake_service)

    resultado = use_case.execute("Videojuegos", min_descuento=10, max_descuento=None, limite=10)

    assert [p.titulo for p in resultado] == ["Descuento muy alto", "Descuento medio"]
