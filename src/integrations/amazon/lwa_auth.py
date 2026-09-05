"""
Autenticación LWA (Login With Amazon) para la Creator's API
La SDK oficial (creatorsapi_python_sdk) trae su propio flujo OAuth2 contra
Cognito, pero las credenciales de este proyecto son de tipo LWA clásico y
solo funcionan contra el endpoint de autenticación de Amazon
(api.amazon.co.uk) con el scope "creatorsapi::default". Este módulo obtiene
y cachea el token de acceso usando ese flujo, para inyectarlo manualmente en
el ApiClient de la SDK (ver amazon_api.py), ya que la SDK no permite
configurar el scope que usa internamente.
"""

import time
import logging
import requests

logger = logging.getLogger(__name__)


class LwaTokenManager:
    """
    Gestiona el token de acceso LWA, cacheándolo hasta que caduca.
    Expone get_token(), la misma interfaz que espera el ApiClient de la SDK.
    """

    def __init__(self, client_id: str, client_secret: str, auth_endpoint: str, scope: str):
        self._client_id = client_id
        self._client_secret = client_secret
        self._auth_endpoint = auth_endpoint
        self._scope = scope
        self._token: str | None = None
        self._expires_at: float = 0.0

    def get_token(self) -> str:
        """Devuelve el token cacheado si sigue siendo válido, o pide uno nuevo."""
        if self._token and time.time() < self._expires_at:
            return self._token
        return self._refresh()

    def _refresh(self) -> str:
        """Pide un token nuevo a Amazon usando el flujo client_credentials de LWA."""
        response = requests.post(
            self._auth_endpoint,
            data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "scope": self._scope,
            },
            timeout=30,
        )
        if response.status_code != 200:
            raise RuntimeError(f"Fallo al obtener token LWA ({response.status_code}): {response.text}")

        data = response.json()
        self._token = data["access_token"]
        # Restamos 30s de margen para refrescar el token antes de que caduque de verdad.
        self._expires_at = time.time() + data.get("expires_in", 3600) - 30
        return self._token
