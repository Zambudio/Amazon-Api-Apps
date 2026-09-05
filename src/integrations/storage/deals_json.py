"""
Almacenamiento de ofertas del barrido en JSON (data/max_ofertas_*.json)
Este módulo centraliza el formato de guardado/lectura de los resultados del
buscador de chollos: lo usan tanto scripts/test_busqueda_max_ofertas.py como
la GUI (deals_gui.py) para que ambos generen y lean el mismo formato.

Los JSON guardan una lista de ofertas en la clave "ofertas", cada una con los
campos: asin, titulo, marca, categoria, precio_actual, precio_anterior,
descuento, valoracion, num_valoraciones, url, imagen y fin_oferta.
"""

import json
import os
from datetime import datetime

from src.domain.entities import ProductInfo


def producto_a_dict(p: ProductInfo) -> dict:
    """Serializa un ProductInfo al formato que guardamos en los JSON de ofertas."""
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


def guardar_ofertas_json(chollos, ruta: str, metadatos: dict = None) -> str:
    """Escribe la lista de ProductInfo en un JSON de ofertas y devuelve la ruta.

    metadatos (opcional) se guarda en la raíz del JSON tal cual (ej.
    min_descuento, detalle_por_categoria) para poder reproducir el contexto
    del barrido al cargarlo más tarde.
    """
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    output = {"timestamp": datetime.now().isoformat()}
    if metadatos:
        output.update(metadatos)
    output["ofertas"] = [producto_a_dict(p) for p in chollos]
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)
    return ruta


def productos_desde_json(ruta: str) -> list[ProductInfo]:
    """Lee un JSON de ofertas y devuelve una lista de ProductInfo para la GUI.

    El dict guardado usa 'url', 'imagen' y 'descuento'; lo adaptamos a los
    campos de ProductInfo (url_afiliado, imagen_principal, descuento_porcentaje).
    """
    with open(ruta, encoding="utf-8") as f:
        data = json.load(f)

    chollos = []
    for o in data.get("ofertas") or []:
        p = ProductInfo()
        p.asin = o.get("asin") or ""
        p.url_afiliado = o.get("url") or ""
        p.titulo = o.get("titulo") or ""
        p.marca = o.get("marca") or ""
        p.categoria = o.get("categoria") or ""
        p.precio_actual = o.get("precio_actual")
        p.precio_anterior = o.get("precio_anterior")
        p.descuento_porcentaje = o.get("descuento")
        p.valoracion = o.get("valoracion")
        p.num_valoraciones = o.get("num_valoraciones")
        p.imagen_principal = o.get("imagen") or ""
        p.fin_oferta = o.get("fin_oferta")
        chollos.append(p)
    return chollos
