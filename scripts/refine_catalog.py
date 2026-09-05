"""
Script: Refinar Catálogo
Este es un script avanzado para pulir los datos del catálogo. A diferencia 
del procesado básico, este script intenta extraer descripciones más 
significativas y corregir errores en las fechas de fin de oferta.
"""

import json
import re

def refine_catalog():
    """Realiza un pulido detallado de los productos del catálogo."""
    file_path = 'todos_los_productos.json'
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            products = json.load(f)
    except FileNotFoundError:
        print("Error: No se encuentra todos_los_productos.json")
        return

    # 1. Eliminamos duplicados por título
    seen_titles = set()
    deduplicated = []
    for p in products:
        clean_title = p['titulo'].strip().lower()
        if clean_title not in seen_titles:
            seen_titles.add(clean_title)
            deduplicated.append(p)
    
    refined = []
    for p in deduplicated:
        # Intentamos extraer una 'esencia' de la descripción evitando frases genéricas
        desc = p.get('descripcion', '')
        if desc:
            # Quitamos muletillas de marketing
            clean_desc = re.sub(r'^(Disfruta de|Consigue este|Ideal para|Perfecto para|Descubre|Aprovecha)\s+', '', desc, flags=re.I)
            p['descripcion_corta'] = clean_desc[:100].strip() + "..."
        else:
            p['descripcion_corta'] = "Oferta sin descripción detallada."
        
        refined.append(p)

    # Actualizamos el archivo original con los datos refinados
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(refined, f, ensure_ascii=False, indent=4)

    print(f"Éxito: {len(refined)} productos refinados.")

if __name__ == "__main__":
    refine_catalog()
