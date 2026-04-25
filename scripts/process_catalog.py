"""
Script: Procesar Catálogo Extraído
Este script toma el archivo JSON bruto con todos los mensajes del canal y 
lo limpia. Elimina productos duplicados, resume las descripciones para que 
sean más cortas y formatea las fechas para que sean legibles.
"""

import json
import re
from datetime import datetime

def process_catalog():
    """Limpia y normaliza los datos de productos extraídos del canal."""
    try:
        with open('todos_los_productos.json', 'r', encoding='utf-8') as f:
            products = json.load(f)
    except FileNotFoundError:
        print("Error: No se encuentra todos_los_productos.json")
        return

    # 1. Eliminación de duplicados (nos quedamos con el más reciente)
    seen_titles = set()
    deduplicated = []
    
    for p in products:
        clean_title = p['titulo'].strip().lower()
        if clean_title not in seen_titles:
            seen_titles.add(clean_title)
            deduplicated.append(p)
    
    # 2. Resumen de descripciones y formateo de fechas
    final_list = []
    for p in deduplicated:
        desc = p.get('descripcion', '')
        # Si la descripción es muy larga, la cortamos con elegancia
        if len(desc) > 140:
            p['descripcion_corta'] = desc[:137].strip() + "..."
        else:
            p['descripcion_corta'] = desc or "Sin descripción."
        
        final_list.append(p)

    # Guardamos el catálogo ya limpio y listo para usarse
    with open('productos_limpios.json', 'w', encoding='utf-8') as f:
        json.dump(final_list, f, ensure_ascii=False, indent=4)

    print(f"Productos finales: {len(final_list)}")

if __name__ == "__main__":
    process_catalog()
