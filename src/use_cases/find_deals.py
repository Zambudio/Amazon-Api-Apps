"""
Caso de Uso: Buscar Chollos por Categoría
Este archivo orquesta la búsqueda de productos en oferta dentro de una
categoría de Amazon (ej. "Videojuegos"). Pide los datos al servicio de
Amazon y aplica un filtro de seguridad adicional por si el porcentaje
mínimo de ahorro solicitado a la API no se respeta con exactitud.

NOTA IMPORTANTE sobre la API (descubierto en la exploración 2026-07-20):
  - La Amazon Creators API v3.2 CAPA itemCount a 10 (aunque la SDK
    documenta un máximo de 100). Cualquier valor >10 devuelve solo 10.
  - itemPage máximo = 10. Por tanto el techo por query es 10×10 = 100.
  - Para maximizar cobertura, rotamos el SortBy: cada criterio de
    ordenación devuelve un subconjunto parcialmente distinto, y
    deduplicando por ASIN obtenemos ~200+ productos únicos por categoría.
  - Además hacemos un barrido por marcas: usamos las marcas de calidad
    curadas relevantes a la categoría (mapa marcas→categorías en domain)
    más las marcas de calidad que aparezcan en los refinements de la API,
    para cubrir las ofertas de marcas reconocidas que pueden quedar fuera
    del ranking de los SortBy.

  - El parámetro min_saving_percent se envía a la API para que solo
    devuelva ofertas ≥ ese umbral (el filtro local se mantiene como red
    de seguridad). Esto evita llenar el cupo de 100/query con descuentos
    marginales de 1-14% que luego se descartan.
"""

import logging
import time
from typing import Optional
from src.services.amazon_service import AmazonService
from src.domain.entities import ProductInfo
from src.domain.marcas_calidad import es_marca_calidad, marcas_para_categoria

logger = logging.getLogger(__name__)

# Máximo real de ítems por página (la API ignora valores >10).
_API_ITEM_COUNT = 10

# Máximo de páginas que acepta la API (1-10).
_API_MAX_PAGES = 10

# Pausa entre peticiones (1 req/s recomendado por Amazon).
_PAUSA_ENTRE_PETICIONES = 1.0

# Límites del barrido por marcas: cuántas marcas probar y cuántas páginas por
# marca. Cada página son 10 ítems; 10 marcas × 2 páginas = hasta 200 ítems
# extra de marcas reconocidas por categoría (vs. ~120 de genéricas antes).
_BRANDS_MAX = 10
_BRANDS_PAGES = 2

# Criterios de ordenación a rotar para ampliar la cobertura de resultados.
# Cada SortBy devuelve un ranking diferente, aportando productos que no
# aparecen en los demás. Con 5 variantes × 10 páginas × 10 ítems, el techo
# teórico pasa de 100 a 500, y en la práctica se obtienen ~200+ únicos.
_SORT_STRATEGIES = [
    None,                     # Featured (por defecto)
    "Price:LowToHigh",
    "Price:HighToLow",
    "NewestArrivals",
    "AvgCustomerReviews",
]


class FindDealsUseCase:
    """Busca y filtra los mejores chollos de una categoría concreta."""

    def __init__(self, amazon_service: AmazonService = None):
        self.amazon_service = amazon_service or AmazonService()

    def execute(
        self,
        categoria: str,
        min_descuento: int = 20,
        max_descuento: Optional[int] = None,
        limite: Optional[int] = 10,
        on_progress: Optional[callable] = None,
        incluir_marcas: bool = True,
        max_marcas: int = _BRANDS_MAX,
        paginas_por_marca: int = _BRANDS_PAGES,
        min_saving_percent_api: Optional[int] = None,
        priorizar_marcas: bool = True,
    ) -> list[ProductInfo]:
        """
        Devuelve los productos de la categoría indicada que cumplen el rango
        de descuento pedido (mínimo, y máximo si se indica), ordenados de
        mayor a menor descuento.

        Rota por varios criterios de SortBy para ampliar la cobertura (cada
        criterio devuelve un conjunto parcialmente distinto de productos) y,
        si incluir_marcas es True, completa con un barrido por las marcas
        de calidad relevantes a la categoría (mapa domain + refinements).

        Args:
            on_progress: callback opcional (msg: str) para informar del
                         progreso al llamante (ej. la GUI).
            incluir_marcas: si True, amplía la cobertura buscando además por
                            las marcas relevantes de la categoría.
            max_marcas: cuántas marcas probar como máximo en el barrido.
            paginas_por_marca: cuántas páginas pedir por cada marca.
            min_saving_percent_api: descuento mínimo (%) que se pide a la API.
                            None (por defecto) = min_descuento. El filtro local
                            se mantiene como red de seguridad.
            priorizar_marcas: si True, las ofertas de marcas de calidad se
                            ordenan antes que el resto (a igual señal, el
                            mayor descuento). El orden pasa de ser solo por
                            descuento a ser "calidad primero, luego descuento".
        """
        # Acumulador deduplicado por ASIN (evita duplicados entre páginas
        # y entre distintos SortBy y marcas).
        productos_dict: dict[str, ProductInfo] = {}

        # Descuento que realmente se pide a Amazon: por defecto el del usuario.
        saving_api = (
            min_saving_percent_api
            if min_saving_percent_api is not None
            else min_descuento
        )

        def _notify(msg: str):
            logger.info(msg)
            if on_progress:
                on_progress(msg)

        try:
            for sort_idx, sort_by in enumerate(_SORT_STRATEGIES):
                sort_label = sort_by or "Featured"
                _notify(
                    f"Buscando en '{categoria}' (orden: {sort_label}, "
                    f"estrategia {sort_idx + 1}/{len(_SORT_STRATEGIES)})"
                )

                for page in range(1, _API_MAX_PAGES + 1):
                    page_items = self.amazon_service.search_deals(
                        categoria=categoria,
                        min_saving_percent=saving_api,
                        item_count=_API_ITEM_COUNT,
                        item_page=page,
                        sort_by=sort_by,
                    )

                    if not page_items:
                        break

                    for p in page_items:
                        productos_dict[p.asin] = p

                    time.sleep(_PAUSA_ENTRE_PETICIONES)

                # Pausa entre estrategias de SortBy
                time.sleep(_PAUSA_ENTRE_PETICIONES)

            if incluir_marcas:
                self._barrido_por_marcas(
                    categoria, productos_dict, max_marcas, paginas_por_marca,
                    saving_api, _notify,
                )

        except ValueError:
            raise
        except Exception:
            logger.exception("Error al buscar chollos en la categoría '%s'", categoria)
            if not productos_dict:
                return []

        _notify(
            f"Encontrados {len(productos_dict)} productos únicos en '{categoria}', "
            f"aplicando filtros de descuento..."
        )

        # Filtro de seguridad: la API puede devolver productos por debajo del
        # umbral pedido, o sin descuento calculado. También descartamos
        # productos sin título o imagen, ya que no son útiles para publicar.
        chollos = [
            p for p in productos_dict.values()
            if (p.titulo and p.imagen_principal
                and p.descuento_porcentaje is not None
                and p.descuento_porcentaje >= min_descuento
                and (max_descuento is None or p.descuento_porcentaje <= max_descuento))
        ]

        self._ordenar_final(chollos, priorizar_marcas)
        return chollos[:limite]

    def _ordenar_final(self, chollos: list[ProductInfo], priorizar_marcas: bool) -> None:
        """Ordena los chollos de mayor a menor descuento; si priorizar_marcas
        es True, las marcas de calidad van primero (a igual señal, mayor
        descuento). In-place."""
        if not priorizar_marcas:
            chollos.sort(key=lambda p: p.descuento_porcentaje, reverse=True)
            return
        chollos.sort(
            key=lambda p: (
                1 if es_marca_calidad(p.marca) else 0,
                p.descuento_porcentaje or 0,
            ),
            reverse=True,
        )

    def _barrido_por_marcas(
        self,
        categoria: str,
        productos_dict: dict[str, ProductInfo],
        max_marcas: int,
        paginas_por_marca: int,
        saving_api: int,
        _notify,
    ) -> None:
        """Amplía la cobertura buscando las ofertas de las marcas de calidad.

        Prioriza las marcas reconocidas que son relevantes a la categoría:
          1. Marcas curadas del mapa marcas→categorías (domain/marcas_calidad).
          2. Marcas de calidad presentes en los refinements de la categoría
             (aunque no estén en el mapa, p.ej. marcas top que sí son buenas).
        Se descartan las marcas genéricas (p.ej. BROTECT, MOKO) que dominan
        los refinements, porque son justo las que llenan el barrido de ruido.
        Si los refinements fallan, seguimos con el mapa sin abortar.
        """
        marcas: list[str] = list(marcas_para_categoria(categoria))

        try:
            refinements = self.amazon_service.get_brand_refinements(categoria)
            marcas_de_refinements = [
                m for m in refinements if es_marca_calidad(m)
            ]
            for m in marcas_de_refinements:
                if m not in marcas:
                    marcas.append(m)
        except Exception:
            logger.exception("No se pudieron obtener las marcas de '%s'", categoria)

        marcas = [marca for marca in marcas if marca][:max_marcas]
        if not marcas:
            return

        _notify(
            f"Ampliando cobertura de '{categoria}' por marcas de calidad: "
            f"{', '.join(marcas)}"
        )

        for marca in marcas:
            for page in range(1, paginas_por_marca + 1):
                page_items = self.amazon_service.search_deals(
                    categoria=categoria,
                    min_saving_percent=saving_api,
                    item_count=_API_ITEM_COUNT,
                    item_page=page,
                    brand=marca,
                )

                if not page_items:
                    break

                for p in page_items:
                    productos_dict[p.asin] = p

                time.sleep(_PAUSA_ENTRE_PETICIONES)

            time.sleep(_PAUSA_ENTRE_PETICIONES)

    def execute_todas(
        self,
        categorias: list[str],
        min_descuento: int = 20,
        max_descuento: Optional[int] = None,
        limite: Optional[int] = 10,
        on_progress: Optional[callable] = None,
        incluir_marcas: bool = True,
        min_saving_percent_api: Optional[int] = None,
        priorizar_marcas: bool = True,
    ) -> list[ProductInfo]:
        """
        Busca chollos en TODAS las categorías indicadas y devuelve los `limite`
        mejores descuentos del conjunto, ordenados de mayor a menor.

        Args:
            on_progress: callback opcional (msg: str) para informar del
                         progreso al llamante (ej. la GUI).
            incluir_marcas: si True, cada categoría amplía su cobertura con el
                            barrido por marcas de calidad.
            min_saving_percent_api: descuento (%) que se pide a la API (None =
                            min_descuento). Se propaga a execute().
            priorizar_marcas: si True, las marcas de calidad se ordenan antes
                            que el resto en el resultado conjunta.
        """
        todos: dict[str, ProductInfo] = {}

        for indice, categoria in enumerate(categorias):
            if on_progress:
                on_progress(
                    f"Categoría {indice + 1}/{len(categorias)}: {categoria}"
                )
            if indice > 0:
                time.sleep(_PAUSA_ENTRE_PETICIONES)

            for p in self.execute(
                categoria,
                min_descuento=min_descuento,
                max_descuento=max_descuento,
                limite=None,  # Sin tope por categoría; filtramos al final
                on_progress=on_progress,
                incluir_marcas=incluir_marcas,
                min_saving_percent_api=min_saving_percent_api,
                priorizar_marcas=priorizar_marcas,
            ):
                todos[p.asin] = p

        chollos = list(todos.values())
        self._ordenar_final(chollos, priorizar_marcas)
        return chollos[:limite]
