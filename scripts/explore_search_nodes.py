"""
Sondeo rápido de sub-nodos y SearchIndex tech (Amazon Creators API).

Para cada categoría actual del mapa obtiene los refinements browse_node
(1 llamada) y, de ahí, los sub-nodos candidatos a tech; después prueba
cada candidato con search_items (minSavingPercent=15, página 1, itemCount 10)
para ver cuántos chollos tech aporta de verdad.

También prueba SearchIndex adicionales de la API que podrían no estar
cubiertos (OfficeProducts, Appliances, Software…).

Uso:  python scripts/explore_search_nodes.py
"""
import sys, os, time, json, logging
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.integrations.amazon.amazon_api import (
    _build_api, _get_token_manager, extraer_producto,
    AFFILIATE_TAG, MARKETPLACE, SEARCH_RESOURCES, _search_items,
)
from src.domain.categories_search_index import CATEGORY_SEARCH_MAP, CATEGORY_DISPLAY_NAMES
from src.integrations.amazon.amazon_api import get_brand_refinements

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

PAUSE = 1.2
MIN_DISC = 15
# Nodos que ya tenemos (no los volvemos a probar)
NODOS_CONOCIDOS = {v["browse_node_id"] for v in CATEGORY_SEARCH_MAP.values() if v.get("browse_node_id")}
SEARCH_INDEX_CONOCIDOS = {v["search_index"] for v in CATEGORY_SEARCH_MAP.values() if v.get("search_index")}

# SearchIndex adicionales de la API de Amazon que podrían aportar tech.
SEARCH_INDEX_CANDIDATOS = ["Appliances", "OfficeProducts", "Software", "Tools", "HomeImprovement"]


def _search_one(search_index=None, browse_node_id=None, keywords=None, min_saving=MIN_DISC):
    """1 search_items (pág1), devuelve (n_ofertas, top_marcas_5)."""
    try:
        api = _build_api()
        from creatorsapi_python_sdk.models.search_items_request_content import SearchItemsRequestContent
        req = SearchItemsRequestContent(
            partnerTag=AFFILIATE_TAG,
            searchIndex=search_index,
            browseNodeId=browse_node_id,
            keywords=keywords,
            minSavingPercent=min_saving,
            itemCount=10,
            itemPage=1,
            resources=SEARCH_RESOURCES,
        )
        resp = api.search_items(MARKETPLACE, req)
        sr = getattr(resp, "search_result", None)
        items = getattr(sr, "items", None) or []
        total = getattr(sr, "total_result_count", None) or 0
        from collections import Counter
        marcas = Counter(
            (getattr(item, "item_info", None) and
             getattr(getattr(item, "item_info", None), "by_line_info", None) and
             getattr(getattr(getattr(item, "item_info", None), "by_line_info", None), "brand", None) and
             getattr(getattr(getattr(getattr(item, "item_info", None), "by_line_info", None), "brand", None), "display_value", "") or "")
            for item in items
        )
        descuentos = []
        for item in items:
            try:
                listings = item.offers_v2.listings
                if listings:
                    l = next((x for x in listings if getattr(x, "is_buy_box_winner", False)), listings[0])
                    pct = getattr(getattr(l, "price", None), "savings", None)
                    if pct:
                        descuentos.append(int(getattr(pct, "percentage", 0)))
            except Exception:
                pass
        desc_medio = sum(descuentos) / len(descuentos) if descuentos else 0
        return {
            "total_api": int(total),
            "items_p1": len(items),
            "marcas_top5": marcas.most_common(5),
            "desc_medio_p1": round(desc_medio, 1),
        }
    except Exception as e:
        logger.debug("Error en search_one: %s", e)
        return {"error": str(e)}


def _get_refinements_browse_nodes(search_index=None, browse_node_id=None):
    """Devuelve sub-nodos desde browse_node refinements (1 llamada)."""
    try:
        api = _build_api()
        from creatorsapi_python_sdk.models.search_items_request_content import SearchItemsRequestContent
        from creatorsapi_python_sdk.models.search_items_resource import SearchItemsResource
        req = SearchItemsRequestContent(
            partnerTag=AFFILIATE_TAG, searchIndex=search_index,
            browseNodeId=browse_node_id, itemCount=1, itemPage=1,
            resources=[SearchItemsResource.SEARCHREFINEMENTS],
        )
        resp = api.search_items(MARKETPLACE, req)
        sr = getattr(resp, "search_result", None)
        refinements = getattr(sr, "search_refinements", None)
        browse = getattr(refinements, "browse_node", None)
        bins = getattr(browse, "bins", []) if browse else []
        return [(getattr(b, "id", None), getattr(b, "display_name", "")) for b in bins if getattr(b, "id", None)]
    except Exception as e:
        logger.debug("Error refinements browse_node: %s", e)
        return []


def _keywords_tech_faltan():
    """Keywords genéricos tech que podrían cubrir categorías no registradas."""
    return ["smart home", "domotica", "router wifi", "impresora", "consola", "portatil gaming", "pc sobremesa", "disco duro externo", "disco ssd", "camara seguridad"]


def main():
    logger.info("=" * 70)
    logger.info("SONDEO DE NODOS Y SEARCHINDEX TECH")
    logger.info("=" * 70)
    todos_sub_nodos: dict[str, dict] = {}
    resultados_si: dict[str, dict] = {}

    # --- 1) Sub-nodos desde browse_node refinements (1 llamada por categoría con nodo) ---
    logger.info("\n── 1. Sub-nodos via refinements ──")
    for clave, config in CATEGORY_SEARCH_MAP.items():
        bn = config.get("browse_node_id")
        if not bn:
            continue
        sub_nodos = _get_refinements_browse_nodes(browse_node_id=bn)
        nuevos = [(nid, nm) for nid, nm in sub_nodos if nid not in NODOS_CONOCIDOS]
        if nuevos:
            logger.info("  %s (%s) → %d hijos nuevos: %s",
                        clave, bn, len(nuevos), [(nm, nid) for nm, nid in nuevos[:8]])
        for nid, nm in nuevos:
            todos_sub_nodos.setdefault(nid, {"id": nid, "name": nm, "source": f"refinement:{clave}"})
        time.sleep(PAUSE)

    # --- 2) Probar search_index adicionales (1 llamada cada uno) ---
    logger.info("\n── 2. SearchIndex adicionales ──")
    for si in SEARCH_INDEX_CANDIDATOS:
        if si in SEARCH_INDEX_CONOCIDOS:
            continue
        res = _search_one(search_index=si)
        logger.info("  %-20s → %s", si, res)
        if not res.get("error") and res.get("items_p1", 0) >= 3:
            resultados_si[si] = res
        time.sleep(PAUSE)

    # --- 3) Probar keywords genéricos tech (1 llamada cada uno) ---
    logger.info("\n── 3. Keywords tech faltantes ──")
    resultados_kw: dict[str, dict] = {}
    for kw in _keywords_tech_faltan():
        res = _search_one(keywords=kw)
        logger.info("  %-25s → %s", kw, res)
        if not res.get("error") and res.get("items_p1", 0) >= 3:
            resultados_kw[kw] = res
        time.sleep(PAUSE)

    # --- 4) De los sub-nodos, probar los más prometedores (1 llamada c/u) ---
    logger.info("\n── 4. Sondeo de sub-nodos candidatos ──")
    resultados_nodos: dict[str, dict] = {}
    for nid, info in list(todos_sub_nodos.items())[:60]:  # máx 60 para no tardar mucho
        res = _search_one(browse_node_id=nid)
        if not res.get("error") and res.get("items_p1", 0) >= 3:
            resultados_nodos[nid] = {**info, **res}
            logger.info("  ✓ %s (%s) → %d ítems, desc medio %.1f%%",
                        info["name"], nid, res["items_p1"], res["desc_medio_p1"])
        else:
            logger.debug("  ✗ %s (%s) → %s", info["name"], nid, res)
        time.sleep(PAUSE)

    # --- 5) Guardar resultados ---
    output = {
        "timestamp": datetime.now().isoformat(),
        "sub_nodos_candidatos": resultados_nodos,
        "search_index_nuevos": resultados_si,
        "keywords_tech": resultados_kw,
    }
    out_path = os.path.join(os.path.dirname(__file__), '..', 'data',
                            f"explore_nodes_{datetime.now():%Y%m%d_%H%M%S}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)

    # Resumen
    logger.info("\n" + "=" * 70)
    logger.info("CANDIDATOS CONFIRMADOS (≥3 ítems, descuento medio ≥15%)")
    logger.info("=" * 70)
    for nid, info in sorted(resultados_nodos.items(), key=lambda x: x[1].get("desc_medio_p1", 0), reverse=True):
        logger.info("  %s (%s) → desc medio %.1f%%",
                    info["name"], nid, info["desc_medio_p1"])
    if resultados_si:
        logger.info("\nSearchIndex nuevos:")
        for si, info in resultados_si.items():
            logger.info("  %s → desc medio %.1f%%", si, info["desc_medio_p1"])
    if resultados_kw:
        logger.info("\nKeywords tech nuevos:")
        for kw, info in resultados_kw.items():
            logger.info("  '%s' → desc medio %.1f%%", kw, info["desc_medio_p1"])
    logger.info("\nResultados guardados en: %s", out_path)


if __name__ == "__main__":
    main()
