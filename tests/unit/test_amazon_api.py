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
        "version": amazon_api.SUPPORTED_CREDENTIAL_VERSIONS[0],
    }
    assert captured["marketplace"] == amazon_api.MARKETPLACE
    assert captured["request_kwargs"]["partnerTag"] == amazon_api.AFFILIATE_TAG
    assert captured["request_kwargs"]["itemIds"] == ["B08TEST123"]
    assert captured["request_kwargs"]["resources"] == amazon_api.RESOURCES


def test_get_product_falls_back_to_next_credential_version(monkeypatch) -> None:
    attempts: list[str] = []
    fake_item = object()

    def fake_get_items(asin: str, credential_version: str):
        attempts.append(credential_version)
        if credential_version == amazon_api.SUPPORTED_CREDENTIAL_VERSIONS[0]:
            raise Exception("invalid_client")
        return [fake_item]

    monkeypatch.setattr(amazon_api, "CREDENTIAL_VERSION", "")
    monkeypatch.setattr(amazon_api, "_get_items_with_credential_version", fake_get_items)
    monkeypatch.setattr(amazon_api, "extraer_producto", lambda item, tag: item)

    product = amazon_api.get_product("B08TEST123")

    assert product is fake_item
    assert attempts == list(amazon_api.SUPPORTED_CREDENTIAL_VERSIONS[:2])
