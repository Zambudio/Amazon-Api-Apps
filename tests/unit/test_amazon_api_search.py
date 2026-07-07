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

    productos = amazon_api.search_products(search_index="Computers", min_saving_percent=25, item_count=5)

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
    assert captured["request_kwargs"]["resources"] == amazon_api.SEARCH_RESOURCES


def test_search_products_returns_empty_list_on_error(monkeypatch) -> None:
    def fake_search_items(*args, **kwargs):
        raise Exception("fallo de red")

    monkeypatch.setattr(amazon_api, "_search_items", fake_search_items)

    productos = amazon_api.search_products(search_index="Computers")

    assert productos == []
