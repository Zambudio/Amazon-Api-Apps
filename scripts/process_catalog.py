
import json
import re
from datetime import datetime

def process_catalog():
    try:
        with open('todos_los_productos.json', 'r', encoding='utf-8') as f:
            products = json.load(f)
    except FileNotFoundError:
        print("Error: No se encuentra todos_los_productos.json")
        return

    # 1. Deduplicación por título (Telethon devuelve de más nuevo a más viejo)
    # Por lo tanto, la primera vez que vemos un título es la versión más reciente.
    seen_titles = set()
    deduplicated = []
    
    for p in products:
        # Normalizamos el título para comparar (quitando espacios y pasando a minúsculas)
        clean_title = p['titulo'].strip().lower()
        if clean_title not in seen_titles:
            seen_titles.add(clean_title)
            deduplicated.append(p)
    
    # 2. Procesamiento de campos adicionales
    meses = {
        "enero": "01", "febrero": "02", "marzo": "03", "abril": "04", 
        "mayo": "05", "junio": "06", "julio": "07", "agosto": "08", 
        "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12"
    }
    
    # Asumimos 2026 como año actual según el contexto
    current_year = "2026"
    
    final_list = []
    for p in deduplicated:
        # --- Descripción Corta ---
        desc = p.get('descripcion', '')
        if desc:
            # Intentamos coger la primera frase con sentido
            frases = desc.split('.')
            short = frases[0].strip()
            if len(short) < 40 and len(frases) > 1:
                short = short + ". " + frases[1].strip()
            
            # Si sigue siendo muy larga o no tiene puntos, limitamos caracteres
            if len(short) > 140:
                short = short[:137].strip() + "..."
            elif not short:
                short = desc[:100].strip() + "..."
        else:
            short = "Sin descripción disponible."
        
        p['descripcion_corta'] = short
        
        # --- Fecha Fin Formateada ---
        # Buscamos "finaliza" (que sacamos del script anterior)
        # Formatos comunes: "28 de abril", "Hoy", "Mañana"
        raw_fin = p.get('finaliza')
        p['fecha_fin'] = None
        
        if raw_fin:
            raw_fin_lower = raw_fin.lower()
            # Patrón: "D de MES"
            match = re.search(r'(\d{1,2})\s+de\s+(\w+)', raw_fin_lower)
            if match:
                dia = match.group(1).zfill(2)
                mes_str = match.group(2)
                mes_num = meses.get(mes_str, "01")
                p['fecha_fin'] = f"{dia}/{mes_num}/{current_year} 23:59"
            elif "hoy" in raw_fin_lower:
                # Si hoy es 20/04/2026
                p['fecha_fin'] = f"20/04/{current_year} 23:59"
            elif "mañana" in raw_fin_lower:
                p['fecha_fin'] = f"21/04/{current_year} 23:59"
            else:
                p['fecha_fin'] = raw_fin # Dejamos el original si no cuadra
        
        final_list.append(p)

    with open('productos_limpios.json', 'w', encoding='utf-8') as f:
        json.dump(final_list, f, ensure_ascii=False, indent=4)

    print(f"--- Resumen de Procesamiento ---")
    print(f"Productos iniciales: {len(products)}")
    print(f"Productos duplicados eliminados: {len(products) - len(final_list)}")
    print(f"Productos finales: {len(final_list)}")
    print(f"Archivo generado: productos_limpios.json")

if __name__ == "__main__":
    process_catalog()
