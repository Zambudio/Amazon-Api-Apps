"""
Pruebas del buscador de productos por categoría.
Este archivo valida que search_products use la firma real de la SDK instalada
sin hacer llamadas de red a Amazon.
"""

from types import SimpleNamespace

from src.integrations.amazon import amazon_api


def test_search_products_uses_sdk_api_client_signature(monkeypatch) -> None:
    captured: dict[str, object] = {}
    fake_item = object()

    class FakeApiClient:
        def __init__(self, **kwargs) -> None:
            captured["api_client_kwargs"] = kwargs

    class FakeDefaultApi:
        def __init__(self, api_client=None) -> None:
            captured["api_client"] = api_client

        def search_items(self, marketplace, request):
            captured["marketplace"] = marketplace
            captured["request"] = request
            return SimpleNamespace(
                search_result=SimpleNamespace(items=[fake_item])
            )

    class FakeSearchItemsRequestContent:
        def __init__(self, **kwargs) -> None:
            captured["request_kwargs"] = kwargs

    monkeypatch.setattr(amazon_api, "ApiClient", FakeApiClient)
    monkeypatch.setattr(amazon_api, "AmazonCreatorsApi", FakeDefaultApi)
    monkeypatch.setattr(amazon_api, "SearchItemsRequestContent", FakeSearchItemsRequestContent)
    monkeypatch.setattr(amazon_api, "extraer_producto", lambda item, tag: {"item": item, "tag": tag})

    productos = amazon_api.search_products(
        search_index="Computers", min_saving_percent=25, item_count=5, item_page=3
    )

    assert productos == [{"item": fake_item, "tag": amazon_api.AFFILIATE_TAG}]
    assert captured["api_client_kwargs"] == {
        "credential_id": amazon_api.CREDENTIAL_ID,
        "credential_secret": amazon_api.CREDENTIAL_SECRET,
        "version": amazon_api.API_VERSION,
    }
    assert captured["marketplace"] == amazon_api.MARKETPLACE
    assert captured["request_kwargs"]["partnerTag"] == amazon_api.AFFILIATE_TAG
    assert captured["request_kwargs"]["searchIndex"] == "Computers"
    assert captured["request_kwargs"]["minSavingPercent"] == 25
    assert captured["request_kwargs"]["itemCount"] == 5
    assert captured["request_kwargs"]["itemPage"] == 3
    assert captured["request_kwargs"]["resources"] == amazon_api.SEARCH_RESOURCES


def test_search_products_acepta_filtro_por_marca(monkeypatch) -> None:
    captured: dict[str, object] = {}
    fake_item = object()

    class FakeSearchItemsRequestContent:
        def __init__(self, **kwargs) -> None:
            captured["request_kwargs"] = kwargs

    class FakeApiClient:
        def __init__(self, **kwargs) -> None:
            pass

    class FakeDefaultApi:
        def __init__(self, api_client=None) -> None:
            pass

        def search_items(self, marketplace, request):
            return SimpleNamespace(search_result=SimpleNamespace(items=[fake_item]))

    monkeypatch.setattr(amazon_api, "ApiClient", FakeApiClient)
    monkeypatch.setattr(amazon_api, "AmazonCreatorsApi", FakeDefaultApi)
    monkeypatch.setattr(amazon_api, "SearchItemsRequestContent", FakeSearchItemsRequestContent)
    monkeypatch.setattr(amazon_api, "extraer_producto", lambda item, tag: {"item": item, "tag": tag})

    amazon_api.search_products(search_index="Electronics", brand="Xiaomi")

    assert captured["request_kwargs"]["brand"] == "Xiaomi"


def test_search_products_sin_marca_envia_none(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeSearchItemsRequestContent:
        def __init__(self, **kwargs) -> None:
            captured["request_kwargs"] = kwargs

    class FakeApiClient:
        def __init__(self, **kwargs) -> None:
            pass

    class FakeDefaultApi:
        def __init__(self, api_client=None) -> None:
            pass

        def search_items(self, marketplace, request):
            return SimpleNamespace(search_result=SimpleNamespace(items=[]))

    monkeypatch.setattr(amazon_api, "ApiClient", FakeApiClient)
    monkeypatch.setattr(amazon_api, "AmazonCreatorsApi", FakeDefaultApi)
    monkeypatch.setattr(amazon_api, "SearchItemsRequestContent", FakeSearchItemsRequestContent)

    amazon_api.search_products(search_index="Electronics")

    assert captured["request_kwargs"]["brand"] is None


def test_get_brand_refinements_extrae_marcas_de_other_refinements(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeSearchItemsRequestContent:
        def __init__(self, **kwargs) -> None:
            captured["request_kwargs"] = kwargs

    class FakeApiClient:
        def __init__(self, **kwargs) -> None:
            pass

    class FakeDefaultApi:
        def __init__(self, api_client=None) -> None:
            pass

        def search_items(self, marketplace, request):
            return SimpleNamespace(search_result=SimpleNamespace(search_refinements=SimpleNamespace(
                other_refinements=[
                    SimpleNamespace(display_name="Marca", bins=[
                        SimpleNamespace(display_name="XIAOMI"),
                        SimpleNamespace(display_name="Samsung"),
                        SimpleNamespace(display_name="Google"),
                    ]),
                    SimpleNamespace(display_name="Descuento", bins=[SimpleNamespace(display_name="10%")]),
                ]
            )))

    monkeypatch.setattr(amazon_api, "ApiClient", FakeApiClient)
    monkeypatch.setattr(amazon_api, "AmazonCreatorsApi", FakeDefaultApi)
    monkeypatch.setattr(amazon_api, "SearchItemsRequestContent", FakeSearchItemsRequestContent)

    marcas = amazon_api.get_brand_refinements(search_index="Electronics")

    assert marcas == ["XIAOMI", "Samsung", "Google"]
    assert captured["request_kwargs"]["resources"] == [amazon_api.SearchItemsResource.SEARCHREFINEMENTS]


def test_get_brand_refinements_sin_marcas_devuelve_vacio(monkeypatch) -> None:
    class FakeApiClient:
        def __init__(self, **kwargs) -> None:
            pass

    class FakeDefaultApi:
        def __init__(self, api_client=None) -> None:
            pass

        def search_items(self, marketplace, request):
            return SimpleNamespace(search_result=SimpleNamespace(search_refinements=SimpleNamespace(
                other_refinements=[SimpleNamespace(display_name="Descuento", bins=[])]
            )))

    monkeypatch.setattr(amazon_api, "ApiClient", FakeApiClient)
    monkeypatch.setattr(amazon_api, "AmazonCreatorsApi", FakeDefaultApi)
    monkeypatch.setattr(amazon_api, "SearchItemsRequestContent", lambda **kwargs: None)

    assert amazon_api.get_brand_refinements(search_index="Electronics") == []


def test_get_brand_refinements_si_falla_devuelve_vacio(monkeypatch) -> None:
    def fake_search_items(*args, **kwargs):
        raise Exception("fallo de red")

    monkeypatch.setattr(amazon_api, "ApiClient", lambda **kwargs: None)
    monkeypatch.setattr(amazon_api, "AmazonCreatorsApi", lambda api_client=None: SimpleNamespace(search_items=fake_search_items))
    monkeypatch.setattr(amazon_api, "SearchItemsRequestContent", lambda **kwargs: None)

    assert amazon_api.get_brand_refinements(search_index="Electronics") == []


def test_search_products_sin_item_page_pide_la_primera_pagina(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeSearchItemsRequestContent:
        def __init__(self, **kwargs) -> None:
            captured["request_kwargs"] = kwargs

    class FakeApiClient:
        def __init__(self, **kwargs) -> None:
            pass

    class FakeDefaultApi:
        def __init__(self, api_client=None) -> None:
            pass

        def search_items(self, marketplace, request):
            return SimpleNamespace(search_result=SimpleNamespace(items=[]))

    monkeypatch.setattr(amazon_api, "ApiClient", FakeApiClient)
    monkeypatch.setattr(amazon_api, "AmazonCreatorsApi", FakeDefaultApi)
    monkeypatch.setattr(amazon_api, "SearchItemsRequestContent", FakeSearchItemsRequestContent)

    amazon_api.search_products(search_index="Computers")

    # Sin item_page explícito, se envía None y la API devuelve la página 1.
    assert captured["request_kwargs"]["itemPage"] is None


def test_search_products_returns_empty_list_on_error(monkeypatch) -> None:
    intentos = []

    def fake_search_items(*args, **kwargs):
        intentos.append(1)
        raise Exception("fallo de red")

    monkeypatch.setattr(amazon_api, "_search_items", fake_search_items)
    monkeypatch.setattr(amazon_api.time, "sleep", lambda segundos: None)

    productos = amazon_api.search_products(search_index="Computers")

    assert productos == []
    # Debe haberse reintentado una vez (2 intentos en total).
    assert len(intentos) == 2


def test_search_products_recupera_tras_un_fallo(monkeypatch) -> None:
    intentos = []
    fake_item = object()

    def fake_search_items(*args, **kwargs):
        intentos.append(1)
        if len(intentos) == 1:
            raise Exception("fallo temporal")
        return [fake_item]

    monkeypatch.setattr(amazon_api, "_search_items", fake_search_items)
    monkeypatch.setattr(amazon_api.time, "sleep", lambda segundos: None)
    monkeypatch.setattr(amazon_api, "extraer_producto", lambda item, tag: {"item": item, "tag": tag})

    productos = amazon_api.search_products(search_index="Computers")

    assert productos == [{"item": fake_item, "tag": amazon_api.AFFILIATE_TAG}]
    assert len(intentos) == 2
