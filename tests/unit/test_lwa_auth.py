"""
Pruebas del gestor de token LWA.
Valida la obtención y el cacheado del token sin hacer llamadas de red reales.
"""

from types import SimpleNamespace

from src.integrations.amazon.lwa_auth import LwaTokenManager


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text

    def json(self):
        return self._json_data


def test_get_token_pide_token_nuevo_la_primera_vez(monkeypatch) -> None:
    captured = {}

    def fake_post(url, data=None, timeout=None):
        captured["url"] = url
        captured["data"] = data
        return FakeResponse(200, {"access_token": "token-1", "expires_in": 3600})

    monkeypatch.setattr("src.integrations.amazon.lwa_auth.requests.post", fake_post)

    manager = LwaTokenManager("client-id", "client-secret", "https://auth.example/token", "scope::default")
    token = manager.get_token()

    assert token == "token-1"
    assert captured["url"] == "https://auth.example/token"
    assert captured["data"] == {
        "grant_type": "client_credentials",
        "client_id": "client-id",
        "client_secret": "client-secret",
        "scope": "scope::default",
    }


def test_get_token_reutiliza_el_token_cacheado(monkeypatch) -> None:
    llamadas = []

    def fake_post(url, data=None, timeout=None):
        llamadas.append(1)
        return FakeResponse(200, {"access_token": "token-1", "expires_in": 3600})

    monkeypatch.setattr("src.integrations.amazon.lwa_auth.requests.post", fake_post)

    manager = LwaTokenManager("client-id", "client-secret", "https://auth.example/token", "scope::default")
    primer_token = manager.get_token()
    segundo_token = manager.get_token()

    assert primer_token == segundo_token == "token-1"
    assert len(llamadas) == 1


def test_get_token_lanza_error_si_falla_la_peticion(monkeypatch) -> None:
    def fake_post(url, data=None, timeout=None):
        return FakeResponse(400, text='{"error":"invalid_client"}')

    monkeypatch.setattr("src.integrations.amazon.lwa_auth.requests.post", fake_post)

    manager = LwaTokenManager("client-id", "client-secret", "https://auth.example/token", "scope::default")

    try:
        manager.get_token()
        assert False, "Se esperaba una excepción"
    except RuntimeError as e:
        assert "invalid_client" in str(e)
