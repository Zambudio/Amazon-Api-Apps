"""
Explorador de ofertas en profundidad (Amazon Creators API) - v2
Este script investiga cuántas ofertas podemos obtener realmente de la API de
Amazon para una categoría, probando varias estrategias: paginación completa,
variación de itemCount, SortBy, keywords, sub-nodos BrowseNodes y refinements.

Uso: python scripts/explore_deals_depth.py [nombre_categoria]
  Ejemplo: python scripts/explore_deals_depth.py "Móviles y accesorios"
  Sin argumento: usa "Móviles y accesorios" por defecto.
"""

import sys
import os
import json
import time
import logging
from datetime import datetime
from typing import Optional
from collections import defaultdict

# Asegurar que el directorio raíz esté en el path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.integrations.amazon.amazon_api import (
    _build_api, _get_token_manager, extraer_producto,
    AFFILIATE_TAG, MARKETPLACE, SEARCH_RESOURCES,
)
from src.domain.categories_search_index import resolve_category, CATEGORY_DISPLAY_NAMES

# Importar modelos de la SDK
from creatorsapi_python_sdk.models.search_items_request_content import SearchItemsRequestContent
from creatorsapi_python_sdk.models.search_items_resource import SearchItemsResource
from creatorsapi_python_sdk.models.get_browse_nodes_request_content import GetBrowseNodesRequestContent
from creatorsapi_python_sdk.models.get_browse_nodes_resource import GetBrowseNodesResource
from creatorsapi_python_sdk.models.sort_by import SortBy

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

# ── Constantes de exploración ──────────────────────────────────────────
MAX_PAGES = 10          # Límite duro de la API
PAUSE_BETWEEN_CALLS = 1.2  # Segundos entre llamadas (evitar throttle)

# SortBy a probar para ampliar cobertura
SORT_STRATEGIES = [
    None,                           # Orden por defecto (Featured)
    SortBy.PRICE_COLON_LOW_TO_HIGH,
    SortBy.PRICE_COLON_HIGH_TO_LOW,
    SortBy.NEWESTARRIVALS,
    SortBy.AVGCUSTOMERREVIEWS,
]


def get_browse_node_children(browse_node_id: str) -> list[dict]:
    """Consulta GetBrowseNodes para obtener los hijos de un nodo.
    
    Devuelve lista de dicts con 'id' y 'display_name' de cada hijo.
    """
    api = _build_api()
    request = GetBrowseNodesRequestContent(
        partnerTag=AFFILIATE_TAG,
        browseNodeIds=[browse_node_id],
        resources=[
            GetBrowseNodesResource.BROWSE_NODES_DOT_CHILDREN,
            GetBrowseNodesResource.BROWSE_NODES_DOT_ANCESTOR,
        ],
    )
    response = api.get_browse_nodes(MARKETPLACE, request)
    
    browse_nodes_result = getattr(response, "browse_nodes_result", None)
    browse_nodes = getattr(browse_nodes_result, "browse_nodes", None) or []
    
    children = []
    parent_info = None
    for node in browse_nodes:
        # Info del nodo padre
        parent_info = {
            "id": getattr(node, "id", None),
            "display_name": getattr(node, "display_name", None),
            "context_free_name": getattr(node, "context_free_name", None),
            "is_root": getattr(node, "is_root", None),
        }
        logger.info(f"  Nodo consultado: {parent_info}")
        
        # Ancestros
        ancestor = getattr(node, "ancestor", None)
        if ancestor:
            logger.info(f"  Ancestro: {getattr(ancestor, 'display_name', '?')} ({getattr(ancestor, 'id', '?')})")
        
        # Hijos
        node_children = getattr(node, "children", None) or []
        for child in node_children:
            child_id = getattr(child, "id", None)
            child_name = getattr(child, "display_name", None) or "Sin nombre"
            if child_id:
                children.append({"id": child_id, "display_name": child_name})
    
    return children


def search_items_raw(
    search_index: Optional[str],
    browse_node_id: Optional[str],
    min_saving_percent: int,
    item_count: int,
    item_page: int,
    sort_by=None,
    keywords: Optional[str] = None,
) -> tuple[list, int, int]:
    """Ejecuta SearchItems y devuelve (items_raw, total_result_count, len_items).
    
    Acepta item_count parametrizable para diagnosticar si la API respeta
    diferentes valores.
    """
    api = _build_api()
    request = SearchItemsRequestContent(
        partnerTag=AFFILIATE_TAG,
        searchIndex=search_index,
        browseNodeId=browse_node_id,
        keywords=keywords,
        minSavingPercent=min_saving_percent,
        sortBy=sort_by,
        itemCount=item_count,
        itemPage=item_page,
        resources=SEARCH_RESOURCES,
    )
    
    response = api.search_items(MARKETPLACE, request)
    search_result = getattr(response, "search_result", None)
    items = getattr(search_result, "items", None) or []
    total_count = getattr(search_result, "total_result_count", None) or 0
    return items, int(total_count), len(items)


def paginate_search(
    search_index: Optional[str],
    browse_node_id: Optional[str],
    min_saving_percent: int = 1,
    item_count: int = 10,
    sort_by=None,
    keywords: Optional[str] = None,
    label: str = "",
    max_pages: int = MAX_PAGES,
) -> tuple[dict, int]:
    """Pagina una búsqueda SearchItems hasta agotar resultados o alcanzar el límite.
    
    IMPORTANTE: No corta prematuramente. Sigue paginando mientras haya
    resultados o hasta alcanzar max_pages, incluso si una página devuelve
    menos del item_count solicitado.
    """
    productos = {}
    total_api = 0
    consecutive_empty = 0
    
    for page in range(1, max_pages + 1):
        try:
            items, total_count, items_len = search_items_raw(
                search_index=search_index,
                browse_node_id=browse_node_id,
                min_saving_percent=min_saving_percent,
                item_count=item_count,
                item_page=page,
                sort_by=sort_by,
                keywords=keywords,
            )
            if page == 1:
                total_api = total_count
                
            for item in items:
                p = extraer_producto(item, AFFILIATE_TAG)
                productos[p.asin] = p
            
            sort_label = sort_by.value if sort_by else "Default"
            logger.info(
                f"  [{label}] p.{page}: {items_len} ítems "
                f"(total API: {total_count}, únicos acum: {len(productos)}, "
                f"sort: {sort_label}, itemCount: {item_count})"
            )
            
            # Solo cortar si la página vino completamente vacía (2 veces seguidas)
            if items_len == 0:
                consecutive_empty += 1
                if consecutive_empty >= 2:
                    logger.info(f"  [{label}] 2 páginas vacías seguidas, parando.")
                    break
            else:
                consecutive_empty = 0
            
            # Si ya hemos acumulado más del total reportado, parar
            if total_count > 0 and len(productos) >= total_count:
                logger.info(f"  [{label}] Alcanzado total reportado ({total_count}), parando.")
                break
                
            time.sleep(PAUSE_BETWEEN_CALLS)
            
        except Exception as e:
            error_str = str(e)
            if "ItemsNotFound" in error_str or "NoResults" in error_str:
                logger.info(f"  [{label}] Sin resultados en página {page}, parando.")
                break
            logger.warning(f"  [{label}] Error en página {page}: {e}")
            break
    
    return productos, total_api


def get_refinement_nodes(search_index: Optional[str], browse_node_id: Optional[str]) -> list[dict]:
    """Obtiene sub-nodos a través de SearchRefinements de una búsqueda."""
    try:
        api = _build_api()
        request = SearchItemsRequestContent(
            partnerTag=AFFILIATE_TAG,
            searchIndex=search_index,
            browseNodeId=browse_node_id,
            minSavingPercent=1,
            itemCount=1,
            itemPage=1,
            resources=[SearchItemsResource.SEARCHREFINEMENTS],
        )
        response = api.search_items(MARKETPLACE, request)
        search_result = getattr(response, "search_result", None)
        refinements = getattr(search_result, "search_refinements", None)
        
        sub_nodes = []
        
        # BrowseNode refinements
        browse_refinement = getattr(refinements, "browse_node", None)
        if browse_refinement:
            bins = getattr(browse_refinement, "bins", None) or []
            for b in bins:
                node_id = getattr(b, "id", None)
                node_name = getattr(b, "display_name", None) or "Sin nombre"
                if node_id:
                    sub_nodes.append({"id": node_id, "display_name": node_name, "source": "refinement_browseNode"})
        
        # SearchIndex refinements
        si_refinement = getattr(refinements, "search_index", None)
        if si_refinement:
            si_bins = getattr(si_refinement, "bins", None) or []
            logger.info(f"  SearchIndex refinements: {len(si_bins)}")
            for b in si_bins:
                logger.info(f"    - {getattr(b, 'display_name', '?')} ({getattr(b, 'id', '?')})")
        
        # Other refinements
        other = getattr(refinements, "other_refinements", None) or []
        for ref in other:
            ref_name = getattr(ref, "display_name", None)
            ref_bins = getattr(ref, "bins", None) or []
            logger.info(f"  Refinamiento '{ref_name}': {len(ref_bins)} bins")
            for b in ref_bins[:5]:
                logger.info(f"    - {getattr(b, 'display_name', '?')} ({getattr(b, 'id', '?')})")
        
        return sub_nodes
    except Exception as e:
        logger.warning(f"  Error obteniendo refinements: {e}")
        return []


def explore_category(categoria_nombre: str) -> dict:
    """Ejecuta todas las estrategias de exploración para una categoría."""
    config = resolve_category(categoria_nombre)
    search_index = config["search_index"]
    browse_node_id = config["browse_node_id"]
    
    results = {
        "categoria": categoria_nombre,
        "search_index": search_index,
        "browse_node_id": browse_node_id,
        "timestamp": datetime.now().isoformat(),
        "estrategias": {},
        "totales": {},
    }
    
    all_products = {}
    
    # ═══════════════════════════════════════════════════════════════════
    # DIAGNÓSTICO: ¿La API respeta itemCount?
    # ═══════════════════════════════════════════════════════════════════
    logger.info("=" * 70)
    logger.info("DIAGNÓSTICO: Verificando itemCount")
    logger.info("=" * 70)
    
    diag_results = {}
    for ic in [1, 5, 10, 50, 100]:
        try:
            items, total, items_len = search_items_raw(
                search_index=search_index,
                browse_node_id=browse_node_id,
                min_saving_percent=1,
                item_count=ic,
                item_page=1,
                sort_by=None,
            )
            logger.info(f"  itemCount={ic:3d} → devuelve {items_len} ítems (totalResultCount={total})")
            diag_results[ic] = {"solicitado": ic, "devuelto": items_len, "total_api": total}
            time.sleep(PAUSE_BETWEEN_CALLS)
        except Exception as e:
            logger.warning(f"  itemCount={ic}: Error - {e}")
            diag_results[ic] = {"solicitado": ic, "error": str(e)}
    
    results["diagnostico_item_count"] = diag_results
    
    # ═══════════════════════════════════════════════════════════════════
    # ESTRATEGIA 1: Paginación completa (10 páginas) con itemCount óptimo
    # ═══════════════════════════════════════════════════════════════════
    # Determinamos el itemCount real que funciona
    max_working_ic = max(
        (ic for ic, r in diag_results.items() if "error" not in r and r["devuelto"] == ic),
        default=10,
    )
    logger.info(f"\n  itemCount máximo efectivo: {max_working_ic}")
    
    logger.info("\n" + "=" * 70)
    logger.info(f"ESTRATEGIA 1: Paginación completa (10 pág × {max_working_ic} ítems)")
    logger.info("=" * 70)
    
    strategy1_products = {}
    strategy1_details = {}
    
    for sort_by in SORT_STRATEGIES:
        sort_label = sort_by.value if sort_by else "Default"
        logger.info(f"\n── SortBy: {sort_label} ──")
        
        productos, total_api = paginate_search(
            search_index=search_index,
            browse_node_id=browse_node_id,
            min_saving_percent=1,
            item_count=max_working_ic,
            sort_by=sort_by,
            label=f"S1/{sort_label}",
        )
        
        nuevos = sum(1 for asin in productos if asin not in strategy1_products)
        strategy1_products.update(productos)
        
        strategy1_details[sort_label] = {
            "total_api": total_api,
            "items_obtenidos": len(productos),
            "nuevos_unicos": nuevos,
            "acumulado": len(strategy1_products),
        }
        
        logger.info(
            f"  → {sort_label}: {len(productos)} ítems, "
            f"{nuevos} nuevos (acumulado: {len(strategy1_products)})"
        )
        time.sleep(PAUSE_BETWEEN_CALLS)
    
    results["estrategias"]["paginacion_sortby"] = {
        "total_unicos": len(strategy1_products),
        "item_count_usado": max_working_ic,
        "detalle_por_sort": strategy1_details,
    }
    all_products.update(strategy1_products)
    
    # ═══════════════════════════════════════════════════════════════════
    # ESTRATEGIA 2: Keywords genéricos para obtener resultados distintos
    # ═══════════════════════════════════════════════════════════════════
    logger.info("\n" + "=" * 70)
    logger.info("ESTRATEGIA 2: Keywords genéricos")
    logger.info("=" * 70)
    
    strategy2_products = {}
    strategy2_details = {}
    
    generic_keywords = ["oferta", "descuento", "smartphone", "funda", "cargador", "protector"]
    
    for kw in generic_keywords:
        logger.info(f"\n── Keyword: '{kw}' ──")
        
        productos, total_api = paginate_search(
            search_index=search_index,
            browse_node_id=browse_node_id,
            min_saving_percent=1,
            item_count=max_working_ic,
            sort_by=None,
            keywords=kw,
            label=f"S2/{kw}",
        )
        
        nuevos_vs_s2 = sum(1 for asin in productos if asin not in strategy2_products)
        nuevos_vs_all = sum(1 for asin in productos if asin not in all_products and asin not in strategy2_products)
        strategy2_products.update(productos)
        
        strategy2_details[kw] = {
            "total_api": total_api,
            "items_obtenidos": len(productos),
            "nuevos_vs_esta_estrategia": nuevos_vs_s2,
            "nuevos_vs_todo": nuevos_vs_all,
        }
        
        logger.info(
            f"  → '{kw}': {len(productos)} ítems, "
            f"{nuevos_vs_s2} nuevos en S2, {nuevos_vs_all} nuevos globales "
            f"(acumulado S2: {len(strategy2_products)})"
        )
        time.sleep(PAUSE_BETWEEN_CALLS)
    
    results["estrategias"]["keywords"] = {
        "total_unicos": len(strategy2_products),
        "detalle_por_keyword": strategy2_details,
    }
    all_products.update(strategy2_products)
    
    # ═══════════════════════════════════════════════════════════════════
    # ESTRATEGIA 3: Sub-nodos via GetBrowseNodes + Refinements
    # ═══════════════════════════════════════════════════════════════════
    logger.info("\n" + "=" * 70)
    logger.info("ESTRATEGIA 3: Sub-nodos (BrowseNodes hijos + Refinements)")
    logger.info("=" * 70)
    
    sub_nodes = []
    
    # 3a: GetBrowseNodes (hijos directos)
    target_node = browse_node_id
    if target_node:
        logger.info(f"\n── 3a: GetBrowseNodes hijos de {target_node} ──")
        try:
            children = get_browse_node_children(target_node)
            logger.info(f"  Encontrados {len(children)} hijos directos")
            for c in children:
                logger.info(f"    - {c['display_name']} ({c['id']})")
                c["source"] = "get_browse_nodes"
            sub_nodes.extend(children)
            time.sleep(PAUSE_BETWEEN_CALLS)
        except Exception as e:
            logger.warning(f"  Error GetBrowseNodes: {e}")
    
    # 3b: SearchRefinements
    logger.info(f"\n── 3b: Refinements de búsqueda ──")
    refinement_nodes = get_refinement_nodes(search_index, browse_node_id)
    logger.info(f"  Encontrados {len(refinement_nodes)} nodos via refinements")
    for rn in refinement_nodes:
        logger.info(f"    - {rn['display_name']} ({rn['id']})")
    
    # Unificar (evitar duplicados)
    seen_ids = set()
    unique_sub_nodes = []
    for sn in sub_nodes + refinement_nodes:
        if sn["id"] not in seen_ids:
            seen_ids.add(sn["id"])
            unique_sub_nodes.append(sn)
    
    time.sleep(PAUSE_BETWEEN_CALLS)
    
    strategy3_products = {}
    strategy3_details = {}
    
    for sn in unique_sub_nodes:
        node_id = sn["id"]
        node_name = sn["display_name"]
        logger.info(f"\n── Sub-nodo: {node_name} ({node_id}) ──")
        
        productos, total_api = paginate_search(
            search_index=None,
            browse_node_id=node_id,
            min_saving_percent=1,
            item_count=max_working_ic,
            sort_by=None,
            label=node_name[:20],
        )
        
        nuevos = sum(1 for asin in productos if asin not in all_products and asin not in strategy3_products)
        strategy3_products.update(productos)
        
        strategy3_details[f"{node_name} ({node_id})"] = {
            "total_api": total_api,
            "items_obtenidos": len(productos),
            "nuevos_globales": nuevos,
            "source": sn.get("source", "unknown"),
        }
        
        logger.info(
            f"  → {node_name}: {len(productos)} ítems, "
            f"{nuevos} nuevos globales (acumulado S3: {len(strategy3_products)})"
        )
        time.sleep(PAUSE_BETWEEN_CALLS)
    
    results["estrategias"]["sub_nodos"] = {
        "total_unicos": len(strategy3_products),
        "num_sub_nodos": len(unique_sub_nodes),
        "detalle_por_nodo": strategy3_details,
    }
    all_products.update(strategy3_products)
    
    # ═══════════════════════════════════════════════════════════════════
    # CONSOLIDACIÓN
    # ═══════════════════════════════════════════════════════════════════
    logger.info("\n" + "=" * 70)
    logger.info("RESULTADOS CONSOLIDADOS")
    logger.info("=" * 70)
    
    con_descuento = {
        asin: p for asin, p in all_products.items()
        if p.descuento_porcentaje is not None and p.descuento_porcentaje > 0
    }
    con_descuento_20 = {
        asin: p for asin, p in all_products.items()
        if p.descuento_porcentaje is not None and p.descuento_porcentaje >= 20
    }
    
    results["totales"] = {
        "total_bruto_todas_estrategias": len(all_products),
        "con_descuento_mayor_0": len(con_descuento),
        "con_descuento_mayor_20": len(con_descuento_20),
        "estrategia1_paginacion_sortby": len(strategy1_products),
        "estrategia2_keywords": len(strategy2_products),
        "estrategia3_sub_nodos": len(strategy3_products),
    }
    
    logger.info(f"  Total bruto (deduplicado): {len(all_products)}")
    logger.info(f"  Con descuento > 0%:  {len(con_descuento)}")
    logger.info(f"  Con descuento >= 20%: {len(con_descuento_20)}")
    logger.info(f"  E1 (paginación+SortBy): {len(strategy1_products)} únicos")
    logger.info(f"  E2 (keywords):          {len(strategy2_products)} únicos")
    logger.info(f"  E3 (sub-nodos):         {len(strategy3_products)} únicos")
    
    # Distribución de descuentos
    rangos = defaultdict(int)
    for p in all_products.values():
        if p.descuento_porcentaje is not None:
            if p.descuento_porcentaje >= 50:
                rangos["50%+"] += 1
            elif p.descuento_porcentaje >= 40:
                rangos["40-49%"] += 1
            elif p.descuento_porcentaje >= 30:
                rangos["30-39%"] += 1
            elif p.descuento_porcentaje >= 20:
                rangos["20-29%"] += 1
            elif p.descuento_porcentaje >= 10:
                rangos["10-19%"] += 1
            elif p.descuento_porcentaje > 0:
                rangos["1-9%"] += 1
        else:
            rangos["sin descuento"] += 1
    
    logger.info("\n  Distribución de descuentos:")
    for rango in ["50%+", "40-49%", "30-39%", "20-29%", "10-19%", "1-9%", "sin descuento"]:
        if rango in rangos:
            logger.info(f"    {rango}: {rangos[rango]} productos")
    
    results["distribucion_descuentos"] = dict(rangos)
    
    # Top 20 por descuento
    top = sorted(
        [p for p in all_products.values() if p.descuento_porcentaje],
        key=lambda p: p.descuento_porcentaje,
        reverse=True,
    )[:20]
    
    logger.info("\n  Top 20 por descuento:")
    for i, p in enumerate(top, 1):
        precio_ant = f"{p.precio_anterior:.2f}€" if p.precio_anterior else "?"
        precio_act = f"{p.precio_actual:.2f}€" if p.precio_actual else "?"
        logger.info(
            f"    {i:2d}. -{p.descuento_porcentaje}%  "
            f"{precio_act} (antes {precio_ant})  "
            f"{p.titulo[:55]}"
        )
    
    results["top_20"] = [
        {
            "asin": p.asin,
            "titulo": p.titulo,
            "precio_actual": p.precio_actual,
            "precio_anterior": p.precio_anterior,
            "descuento": p.descuento_porcentaje,
            "url": p.url_afiliado,
        }
        for p in top
    ]
    
    # Serializar todos los productos
    results["productos"] = [
        {
            "asin": p.asin,
            "titulo": p.titulo,
            "marca": p.marca,
            "precio_actual": p.precio_actual,
            "precio_anterior": p.precio_anterior,
            "descuento": p.descuento_porcentaje,
            "categoria": p.categoria,
            "valoracion": p.valoracion,
            "num_valoraciones": p.num_valoraciones,
            "url": p.url_afiliado,
            "imagen": p.imagen_principal,
        }
        for p in all_products.values()
    ]
    
    # Exportar JSON
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(output_dir, exist_ok=True)
    
    safe_name = "".join(c if c.isalnum() or c in "_- " else "" for c in categoria_nombre.lower()).replace(" ", "_")
    output_file = os.path.join(output_dir, f"explore_{safe_name}_{datetime.now():%Y%m%d_%H%M%S}.json")
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    logger.info(f"\n  Resultados exportados a: {output_file}")
    
    return results


def main():
    """Punto de entrada: ejecuta la exploración para la categoría indicada."""
    if len(sys.argv) > 1:
        categoria = sys.argv[1]
    else:
        categoria = "Móviles y accesorios"
    
    logger.info(f"Explorando ofertas en profundidad para: '{categoria}'")
    logger.info(f"Categorías disponibles: {', '.join(CATEGORY_DISPLAY_NAMES)}")
    logger.info("")
    
    try:
        results = explore_category(categoria)
        
        logger.info("\n" + "=" * 70)
        logger.info("RESUMEN FINAL")
        logger.info("=" * 70)
        logger.info(f"  Categoría: {categoria}")
        logger.info(f"  Total ofertas únicas: {results['totales']['total_bruto_todas_estrategias']}")
        logger.info(f"  Con descuento >= 20%: {results['totales']['con_descuento_mayor_20']}")
        logger.info(f"  Diagnóstico itemCount: {results.get('diagnostico_item_count', {})}")
        logger.info("=" * 70)
        
    except ValueError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error inesperado: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
