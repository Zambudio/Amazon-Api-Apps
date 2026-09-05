"""
Prueba de barrido máximo de ofertas (Amazon Creators API)
Este script ejecuta la búsqueda real de chollos (FindDealsUseCase, el mismo
camino que usa run_deals_gui.py: rotación de SortBy + barrido por marcas)
sobre una o varias categorías y exporta un JSON con TODAS las ofertas únicas
encontradas, listas para valorarlas con Keepa.

Uso: python scripts/test_busqueda_max_ofertas.py [categoria] [categoria2 ...]
  - Sin argumentos: busca en TODAS las categorías (19, ~15-40 min).
  - Con argumentos: solo en esas categorías (ej. "Móviles y accesorios").

Opciones:
  --min 15        Descuento mínimo (%) — también se pide a la API salvo --api-min
  --max 50        Descuento máximo (%) — omitir para no fijar tope
  --api-min N     Descuento % que se pide a la API para reducir el ruido de
                  ofertas marginales (por defecto = --min)
  --sin-marcas    Desactiva el barrido por marcas (solo SortBy)
  --max-marcas 8  Marcas de calidad a probar por categoría en el barrido
  --paginas-marca 2  Páginas por marca en el barrido
  --sin-priorizar-marcas  Desactiva el orden con prioridad de marcas de calidad
  --marcas-calidad     Descarta las marcas que no están en la lista de
                        calidad (src/domain/marcas_calidad.py), tras el barrido
"""

import sys
import os
import argparse
import logging
from collections import defaultdict
from datetime import datetime

# Asegurar que el directorio raíz esté en el path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.use_cases.find_deals import FindDealsUseCase
from src.use_cases.filter_chollos_calidad import FilterChollosCalidadUseCase
from src.domain.categories_search_index import CATEGORY_DISPLAY_NAMES
from src.integrations.storage.deals_json import guardar_ofertas_json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Configuración para la consola de Windows
if sys.stdout is not None and getattr(sys.stdout, 'encoding', None) != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, Exception):
        pass


def _resumen_producto(p) -> dict:
    """Serializa un ProductInfo a un dict legible (para el JSON de salida)."""
    return {
        "asin": p.asin,
        "titulo": p.titulo,
        "marca": p.marca,
        "categoria": p.categoria,
        "precio_actual": p.precio_actual,
        "precio_anterior": p.precio_anterior,
        "descuento": p.descuento_porcentaje,
        "valoracion": p.valoracion,
        "num_valoraciones": p.num_valoraciones,
        "url": p.url_afiliado,
        "imagen": p.imagen_principal,
        "fin_oferta": p.fin_oferta,
    }


def main():
    parser = argparse.ArgumentParser(description="Barrido máximo de ofertas de Amazon")
    parser.add_argument("categorias", nargs="*", help="Nombres de categoría (por defecto: todas)")
    parser.add_argument("--min", type=int, default=15, dest="min_descuento")
    parser.add_argument("--max", type=int, default=None, dest="max_descuento")
    parser.add_argument("--sin-marcas", action="store_true", dest="sin_marcas")
    parser.add_argument("--max-marcas", type=int, default=8)
    parser.add_argument("--paginas-marca", type=int, default=2)
    parser.add_argument("--marcas-calidad", action="store_true", dest="marcas_calidad")
    parser.add_argument(
        "--api-min", type=int, default=None, dest="api_min",
        help="Descuento % que se pide a la API (por defecto = --min). Un valor "
             "mayor reduce el ruido de ofertas marginales en el barrido.",
    )
    parser.add_argument(
        "--sin-priorizar-marcas", action="store_true", dest="sin_priorizar_marcas",
        help="Desactiva el orden con prioridad de marcas de calidad "
             "(por defecto las marcas de calidad van delante).",
    )
    args = parser.parse_args()
    priorizar_marcas = not args.sin_priorizar_marcas

    if args.categorias:
        categorias = args.categorias
        # Validar nombres (resolve_category normaliza acentos/mayúsculas).
        for c in categorias:
            from src.domain.categories_search_index import resolve_category
            resolve_category(c)
    else:
        categorias = CATEGORY_DISPLAY_NAMES

    n = len(categorias)
    # Estimación de duración: cada categoría hace ~5 estrategias × hasta 10
    # páginas + max_marcas × paginas_marca llamadas de marca, a ~1 req/s.
    est_llamadas_por_cat = 5 * 10 + args.max_marcas * args.paginas_marca
    est_minutos = round(n * est_llamadas_por_cat * 1.2 / 60, 1)

    logger.info("=" * 70)
    logger.info("BARRIDO MÁXIMO DE OFERTAS")
    logger.info("=" * 70)
    logger.info(f"Categorías ({n}): {', '.join(categorias)}")
    logger.info(f"Descuento: {'>= ' + str(args.min_descuento) + '%' if args.max_descuento is None else f'{args.min_descuento}-{args.max_descuento}%'}")
    logger.info(f"Barrido por marcas: {'OFF' if args.sin_marcas else f'ON (max {args.max_marcas}, {args.paginas_marca} pág/marca)'}")
    logger.info(f"Descuento pedido a la API: {args.api_min if args.api_min is not None else args.min_descuento}%")
    logger.info(f"Prioridad de marcas de calidad en el orden: {'ON' if priorizar_marcas else 'OFF'}")
    if args.marcas_calidad:
        logger.info("Filtro de marcas de calidad (tras el barrido): ON")
    logger.info(f"Tiempo estimado: ~{est_minutos} min")
    logger.info("=" * 70)

    use_case = FindDealsUseCase()
    todos: dict[str, object] = {}
    detalle_por_categoria: dict[str, dict] = {}

    try:
        for indice, categoria in enumerate(categorias, 1):
            logger.info("")
            logger.info("── [%d/%d] %s ──", indice, n, categoria)
            try:
                chollos = use_case.execute(
                    categoria,
                    min_descuento=args.min_descuento,
                    max_descuento=args.max_descuento,
                    limite=None,
                    incluir_marcas=not args.sin_marcas,
                    max_marcas=args.max_marcas,
                    paginas_por_marca=args.paginas_marca,
                    min_saving_percent_api=args.api_min,
                    priorizar_marcas=priorizar_marcas,
                )
            except ValueError as e:
                logger.error("Categoría desconocida: %s", e)
                continue
            except Exception as e:
                logger.error("Error buscando en '%s': %s", categoria, e)
                continue

            nuevos = sum(1 for p in chollos if p.asin not in todos)
            for p in chollos:
                todos[p.asin] = p
            logger.info(
                "  → %d ofertas en esta categoría, %d nuevas (acumulado: %d)",
                len(chollos), nuevos, len(todos),
            )
            detalle_por_categoria[categoria] = {
                "ofertas_en_categoria": len(chollos),
                "nuevas_globales": nuevos,
                "mejor_descuento": max((p.descuento_porcentaje or 0 for p in chollos), default=0),
            }

    except KeyboardInterrupt:
        logger.warning("Interrumpido por el usuario; guardando lo acumulado...")

    # ── Consolidar resultados ──────────────────────────────────────────
    logger.info("")
    logger.info("=" * 70)
    logger.info("RESULTADOS")
    logger.info("=" * 70)
    logger.info(f"Total de ofertas únicas (descuento >= {args.min_descuento}%): {len(todos)}")

    # ── Filtro de calidad opcional (solo marcas de la lista) ────────────
    if args.marcas_calidad:
        antes = len(todos)
        filtradas = FilterChollosCalidadUseCase().execute(list(todos.values()))
        todos = {p.asin: p for p in filtradas}
        logger.info("Filtro de marcas de calidad: %d → %d ofertas", antes, len(todos))

    rangos = defaultdict(int)
    for p in todos.values():
        d = p.descuento_porcentaje or 0
        if d >= 50:
            rangos["50%+"] += 1
        elif d >= 40:
            rangos["40-49%"] += 1
        elif d >= 30:
            rangos["30-39%"] += 1
        elif d >= 20:
            rangos["20-29%"] += 1
        else:
            rangos["<20%"] += 1
    for rango in ["50%+", "40-49%", "30-39%", "20-29%", "<20%"]:
        if rango in rangos:
            logger.info("  %s: %d ofertas", rango, rangos[rango])

    # Señal de calidad: cuántas ofertas son de marcas reconocidas (la lista
    # de src/domain/marcas_calidad.py). Útil para calibrar el barrido.
    from src.domain.marcas_calidad import es_marca_calidad
    n_calidad = sum(1 for p in todos.values() if es_marca_calidad(p.marca))
    pct_calidad = 100 * n_calidad / len(todos) if todos else 0
    logger.info("  Ofertas de marcas de calidad: %d / %d (%.0f%%)", n_calidad, len(todos), pct_calidad)

    top = sorted(
        (p for p in todos.values() if p.descuento_porcentaje),
        key=lambda p: p.descuento_porcentaje,
        reverse=True,
    )[:20]
    logger.info("\n  Top 20 por descuento:")
    for i, p in enumerate(top, 1):
        ant = f"{p.precio_anterior:.2f}€" if p.precio_anterior else "?"
        act = f"{p.precio_actual:.2f}€" if p.precio_actual else "?"
        logger.info("  %2d. -%d%%  %s (antes %s)  %s  [%s]  %s", i, p.descuento_porcentaje, act, ant, p.titulo[:50], p.asin, p.marca)

    # ── Exportar JSON ──────────────────────────────────────────────────
    # Usamos el módulo compartido de storage para que el formato sea idéntico
    # al que genera la GUI (data/max_ofertas_*.json, editable con el botón
    # "📂 Cargar resultados").
    metadatos = {
        "categorias": categorias,
        "min_descuento": args.min_descuento,
        "max_descuento": args.max_descuento,
        "incluir_marcas": not args.sin_marcas,
        "api_min": args.api_min,
        "priorizar_marcas": priorizar_marcas,
        "marcas_calidad": args.marcas_calidad,
        "totales": {
            "ofertas_unicas": len(todos),
            "distribucion_descuentos": dict(rangos),
        },
        "detalle_por_categoria": detalle_por_categoria,
        "top_20": [_resumen_producto(p) for p in top],
    }

    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    output_file = os.path.join(output_dir, f"max_ofertas_{datetime.now():%Y%m%d_%H%M%S}.json")
    guardar_ofertas_json(list(todos.values()), output_file, metadatos=metadatos)

    logger.info("")
    logger.info("Resultados exportados a: %s", output_file)
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
