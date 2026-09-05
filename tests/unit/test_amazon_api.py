"""
Pruebas del adaptador de Amazon.
Este archivo valida que la integración use la firma real de la SDK instalada
sin hacer llamadas de red a Amazon.
"""

from types import SimpleNamespace

from src.integrations.amazon import amazon_api


def test_get_product_uses_sdk_api_client_signature(monkeypatch) -> None:
    captured: dict[str, object] = {}
    fake_item = object()

    class FakeApiClient:
        def __init__(self, **kwargs) -> None:
            captured["api_client_kwargs"] = kwargs

    class FakeDefaultApi:
        def __init__(self, api_client=None) -> None:
            captured["api_client"] = api_client

        def get_items(self, marketplace, request):
            captured["marketplace"] = marketplace
            captured["request"] = request
            return SimpleNamespace(
                items_result=SimpleNamespace(items=[fake_item])
            )

    class FakeGetItemsRequestContent:
        def __init__(self, **kwargs) -> None:
            captured["request_kwargs"] = kwargs

    monkeypatch.setattr(amazon_api, "ApiClient", FakeApiClient)
    monkeypatch.setattr(amazon_api, "AmazonCreatorsApi", FakeDefaultApi)
    monkeypatch.setattr(amazon_api, "GetItemsRequestContent", FakeGetItemsRequestContent)
    monkeypatch.setattr(amazon_api, "extraer_producto", lambda item, tag: {"item": item, "tag": tag})

    product = amazon_api.get_product("B08TEST123")

    assert product == {"item": fake_item, "tag": amazon_api.AFFILIATE_TAG}
    assert captured["api_client_kwargs"] == {
        "credential_id": amazon_api.CREDENTIAL_ID,
        "credential_secret": amazon_api.CREDENTIAL_SECRET,
        "version": amazon_api.API_VERSION,
    }
    assert captured["marketplace"] == amazon_api.MARKETPLACE
    assert captured["request_kwargs"]["partnerTag"] == amazon_api.AFFILIATE_TAG
    assert captured["request_kwargs"]["itemIds"] == ["B08TEST123"]
    assert captured["request_kwargs"]["resources"] == amazon_api.RESOURCES
    # El cliente de la SDK debe llevar inyectado nuestro propio gestor de token LWA,
    # en vez de dejar que la SDK use su flujo OAuth2/Cognito por defecto.
    assert captured["api_client"]._token_manager is amazon_api._get_token_manager()


def test_get_product_returns_none_on_error(monkeypatch) -> None:
    def fake_get_items(asin: str):
        raise Exception("fallo de red")

    monkeypatch.setattr(amazon_api, "_get_items", fake_get_items)

    product = amazon_api.get_product("B08TEST123")

    assert product is None
