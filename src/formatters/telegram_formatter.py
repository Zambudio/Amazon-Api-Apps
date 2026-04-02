from src.domain.entities import ProductInfo

def format_telegram_message(product: ProductInfo) -> str:
    """
    Toma un objeto ProductInfo y devuelve el texto formateado
    tal como se espera en el canal de Telegram, extraído del comportamiento de Consulta.py
    """
    title = product.titulo or "Título no disponible"
    moneda = "€" if product.moneda == "EUR" else product.moneda
    
    price = f"{product.precio_actual:.2f} {moneda}" if product.precio_actual else "Precio no disponible"
    list_price = f"{product.precio_anterior:.2f} {moneda}" if product.precio_anterior else "0,00 €"
    
    ahorro = "0 €"
    if product.precio_actual and product.precio_anterior and product.precio_anterior > product.precio_actual:
        diff = product.precio_anterior - product.precio_actual
        ahorro = f"{diff:.2f} {moneda}"
        
    savings_pct = str(product.descuento_porcentaje) if product.descuento_porcentaje else "0"
    
    url = product.url_afiliado or "URL_NO_DISPONIBLE"
    
    # Tomar la descripción sintetizada por IA si existe, sino la primera característica o nada
    if product.descripcion_gpt:
        description = product.descripcion_gpt.lstrip().replace('\t', ' ').replace('\n', ' ').strip()
    elif product.descripcion:
        description = product.descripcion[0].lstrip().replace('\t', ' ').replace('\n', ' ').strip()
    else:
        description = "Sin descripción técnica adicional."
        
    # Limpiar cualquier separador raro extra introducido por la IA
    description = description.lstrip()
        
    # Usando los emojis de la imagen de ejemplo de Consulta.py
    mensaje = f"🍄 {title}\n\n"
    if product.precio_anterior:
        mensaje += f"💶 Precio: {price} (antes {list_price})\n"
    else:
        mensaje += f"💶 Precio: {price}\n"
        
    if savings_pct != "0":
        mensaje += f"💰 Ahorro: {ahorro} | -{savings_pct}%\n\n"
    else:
        if ahorro != "0 €":
            mensaje += f"💰 Ahorro: {ahorro}\n\n"
        else:
            mensaje += "\n"
            
    mensaje += f"🛒 {url}\n\n"
    # Pegamos el emoji directamente al texto sin espacio intermedio para compensar el "hueco" del custom emoji
    clean_desc = description.lstrip()
    mensaje += f"✏️{clean_desc}\n\n"
    
    if product.fin_oferta:
        try:
            from datetime import datetime
            # Reemplazar Z por +00:00 para parseo compatible y extraer la fecha
            iso_str = product.fin_oferta.replace('Z', '+00:00')
            dt = datetime.fromisoformat(iso_str)
            meses = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
            fecha_str = f"{dt.day} de {meses[dt.month]}"
            mensaje += f"⚠️ Finaliza el {fecha_str}\n\n"
        except Exception:
            mensaje += f"⚠️ Finaliza el {product.fin_oferta[:10]}\n\n"
            
    # Opcional: Generación de categoría
    categoria = product.categoria.split(" > ")[-1] if product.categoria else "CategoriaAutogenerada"
    tag = categoria.replace(" ", "").replace(",", "")
    mensaje += f"#{tag}\n"
    
    return mensaje

def format_text_with_custom_emojis(text: str) -> dict:
    """
    Toma un texto plano final (con emojis nativos incluidos) y calcula 
    los offsets en UTF-16 requeridos por Telegram para generar 'entities' premium.
    Retorna un diccionario de la forma {"text": str, "entities": [...]}.
    """
    from src.integrations.telegram.emoji_mapper import CUSTOM_EMOJI_MAP
    
    entities = []
    
    # Telegram espera los offsets de las 'entities' calculados no en caracteres sueltos,
    # sino en unidades de código (code units) UTF-16.
    
    for emoji_char, custom_id in CUSTOM_EMOJI_MAP.items():
        start = 0
        while True:
            # Buscamos cada ocurrencia del emoji en el texto
            idx = text.find(emoji_char, start)
            if idx == -1:
                break
                
            # Extraemos la subcadena hasta el emoji
            prefix = text[:idx]
            
            # El offset en UTF-16 es la cantidad de bytes en utf-16-le dividido entre 2
            offset = len(prefix.encode('utf-16-le')) // 2
            length = len(emoji_char.encode('utf-16-le')) // 2
            
            entities.append({
                "type": "custom_emoji",
                "offset": offset,
                "length": length,
                "custom_emoji_id": custom_id
            })
            
            start = idx + len(emoji_char)

    return {
        "text": text,
        "entities": entities
    }
