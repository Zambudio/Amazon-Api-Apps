"""
Puerto de Repositorio de Histórico Keepa
Este archivo define el contrato para obtener el histórico de precios de un
conjunto de ASINs desde la API de datos de Keepa. El caso de uso filtra
chollos usando ese histórico; la implementación concreta (la librería `keepa`)
vive en src/integrations/keepa/ y se inyecta por constructor.
"""

from abc import ABC, abstractmethod
from typing import Optional


class KeepaRepository(ABC):
    """Interfaz abstracta para consultar históricos de precios de Keepa."""

    @abstractmethod
    def obtener_historial(self, asins: list[str], dias: int = 90) -> Optional[dict]:
        """
        Consulta el histórico de precios de los ASINs dados.

        Devuelve {asin: (tiempos, precios)} con la serie de precio nuevo
        (NEW, o AMAZON si no hay) de los últimos `dias` días. Devuelve None
        solo si la consulta falló por completo (sin API key, red, etc.); los
        ASINs concretos sin histórico simplemente no aparecen en el dict.
        """
        raise NotImplementedError
