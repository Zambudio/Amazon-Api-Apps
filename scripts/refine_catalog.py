
import json
import re

def refine_catalog():
    file_path = 'todos_los_productos.json'
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            products = json.load(f)
    except FileNotFoundError:
        print("Error: No se encuentra todos_los_productos.json")
        return

    # 1. Deduplicación por título (Mantener el más reciente)
    seen_titles = set()
    deduplicated = []
    for p in products:
        clean_title = p['titulo'].strip().lower()
        if clean_title not in seen_titles:
            seen_titles.add(clean_title)
            deduplicated.append(p)
    
    # 2. Diccionarios y configuraciones
    meses_map = {
        "enero": "01", "febrero": "02", "marzo": "03", "abril": "04", 
        "mayo": "05", "junio": "06", "julio": "07", "agosto": "08", 
        "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12"
    }
    current_year = "2026"
    
    refined = []
    for p in deduplicated:
        # --- REFINAR DESCRIPCIÓN CORTA ---
        # En lugar de solo cortar, buscamos palabras clave para resumir la esencia
        desc = p.get('descripcion', '')
        short_desc = ""
        if desc:
            # Eliminamos frases introductorias típicas
            clean_desc = re.sub(r'^(Disfruta de|Consigue este|Ideal para|Perfecto para|Descubre|Aprovecha)\s+', '', desc, flags=re.I)
            
            # Buscamos la primera parte descriptiva real
            parts = re.split(r'[,.!] \s*', clean_desc)
            if parts:
                # Intentamos construir una frase con sujeto + característica
                core = parts[0].strip()
                if len(core) < 30 and len(parts) > 1:
                    core += " con " + parts[1].strip()
                
                # Aseguramos que empiece en mayúscula y termine en punto
                short_desc = core[0].upper() + core[1:]
                if not short_desc.endswith('.'): short_desc += '.'
            
            # Límite de seguridad
            if len(short_desc) > 100:
                short_desc = short_desc[:97] + "..."
        else:
            short_desc = "Producto en oferta sin descripción detallada."
        
        p['descripcion_corta'] = short_desc

        # --- REFINAR FECHA FIN ---
        # Buscamos en todo el texto del post (si lo tuviéramos) o en el campo "finaliza" que extrajimos
        # El campo "finaliza" del JSON anterior ya contenía el trozo "28 de abril" en algunos casos
        raw_fin = p.get('finaliza')
        formatted_fin = None
        
        if raw_fin:
            # Limpiamos posibles ruidos
            clean_fin = raw_fin.lower().replace('finaliza el', '').replace('⚠️', '').strip()
            
            # Caso: "28 de abril"
            match = re.search(r'(\d{1,2})\s+de\s+(\w+)', clean_fin)
            if match:
                dia = match.group(1).zfill(2)
                mes_str = match.group(2)
                mes_num = meses_map.get(mes_str, "01")
                formatted_fin = f"{dia}/{mes_num}/{current_year} 23:59"
            elif "hoy" in clean_fin:
                formatted_fin = f"20/04/{current_year} 23:59"
            elif "mañana" in clean_fin:
                formatted_fin = f"21/04/{current_year} 23:59"
            else:
                # Si el campo ya venía con algo pero no parseó, intentamos mantenerlo si parece fecha
                if '/' in clean_fin and len(clean_fin) > 4:
                    formatted_fin = clean_fin
        
        # Actualizamos campos (eliminamos los temporales para limpiar el JSON)
        p['fecha_fin'] = formatted_fin
        if 'finaliza' in p: del p['finaliza']
        
        refined.append(p)

    # Sobreescribimos el archivo original
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(refined, f, ensure_ascii=False, indent=4)

    print(f"Éxito: {len(refined)} productos actualizados en {file_path}")

if __name__ == "__main__":
    refine_catalog()
