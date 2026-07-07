"""
Caso de Uso: Buscar Chollos por Categoría
Este archivo orquesta la búsqueda de productos en oferta dentro de una
categoría de Amazon (ej. "Videojuegos"). Pide los datos al servicio de
Amazon y aplica un filtro de seguridad adicional por si el porcentaje
mínimo de ahorro solicitado a la API no se respeta con exactitud.
"""

import logging
from typing import Optional
from src.services.amazon_service import AmazonService
from src.domain.entities import ProductInfo

logger = logging.getLogger(__name__)


class FindDealsUseCase:
    """Busca y filtra los mejores chollos de una categoría concreta."""

    def __init__(self, amazon_service: AmazonService = None):
        self.amazon_service = amazon_service or AmazonService()

    def execute(
        self,
        categoria: str,
        min_descuento: int = 20,
        max_descuento: Optional[int] = None,
        limite: int = 10,
    ) -> list[ProductInfo]:
        """
        Devuelve los productos de la categoría indicada que cumplen el rango
        de descuento pedido (mínimo, y máximo si se indica), ordenados de
        mayor a menor descuento.
        """
        try:
            # No reenviamos min_descuento como filtro a la API de Amazon: su
            # parámetro minSavingPercent combinado con browseNodeId es poco
            # fiable (para muchos umbrales altos devuelve 0 productos aunque
            # sí existan ofertas que los cumplirían). Pedimos siempre con un
            # umbral bajo fijo para traer el mayor número posible de ofertas
            # y aplicamos el umbral real del usuario en el filtro local.
            productos = self.amazon_service.search_deals(
                categoria=categoria,
                min_saving_percent=1,
                item_count=limite,
            )
        except ValueError:
            raise
        except Exception:
            logger.exception("Error al buscar chollos en la categoría '%s'", categoria)
            return []

        # Filtro de seguridad: la API puede devolver productos por debajo del
        # umbral pedido, o sin descuento calculado. También descartamos
        # productos sin título o imagen, ya que no son útiles para publicar.
        # El descuento mínimo/máximo pedido por el usuario se aplica siempre
        # aquí, en el cliente (ver motivo arriba).
        chollos = [
            p for p in productos
            if p.titulo and p.imagen_principal
            and p.descuento_porcentaje is not None
            and p.descuento_porcentaje >= min_descuento
            and (max_descuento is None or p.descuento_porcentaje <= max_descuento)
        ]

        chollos.sort(key=lambda p: p.descuento_porcentaje, reverse=True)
        return chollos[:limite]
