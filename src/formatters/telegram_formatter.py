"""
Formateador de Mensajes para Telegram
Este archivo se encarga de convertir la información técnica de un producto 
en un mensaje bonito y atractivo para los usuarios de Telegram. Añade 
emojis, calcula ahorros y prepara el texto para que incluya iconos premium.
"""

from src.domain.entities import ProductInfo

def format_telegram_message(product: ProductInfo) -> str:
    """
    Construye el texto del post a partir de los datos del producto de Amazon.
    Añade el título, precios, porcentajes de descuento y la descripción resumida.
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
    
    # Prioridad: 1. Descripción resumida por GPT, 2. Primera característica de Amazon, 3. Texto genérico
    if product.descripcion_gpt:
        description = product.descripcion_gpt.lstrip().replace('\t', ' ').replace('\n', ' ').strip()
    elif product.descripcion:
        description = product.descripcion[0].lstrip().replace('\t', ' ').replace('\n', ' ').strip()
    else:
        description = "Sin descripción técnica adicional."
        
    description = description.lstrip()
        
    # Construcción del cuerpo del mensaje con emojis visuales
    mensaje = f"🍄 {title}\n\n"
    if product.precio_anterior:
        mensaje += f"💶 Precio: {price} (antes {list_price})\n"
    else:
        mensaje += f"💶 Precio: {price}\n"
        
    if savings_pct != "0":
        mensaje += f"💰 Ahorro: {ahorro} | -{savings_pct} %\n\n"
    else:
        if ahorro != "0 €":
            mensaje += f"💰 Ahorro: {ahorro}\n\n"
        else:
            mensaje += "\n"
            
    mensaje += f"🛒 {url}\n\n"
    # Pegamos el emoji directamente al texto para que el diseño premium se vea compacto
    clean_desc = description.lstrip()
    mensaje += f"✏️{clean_desc}\n\n"
    
    # Cálculo de la fecha de fin de oferta si está disponible
    if product.fin_oferta:
        try:
            from datetime import datetime
            # Convertimos el formato de fecha de Amazon a algo legible en español
            iso_str = product.fin_oferta.replace('Z', '+00:00')
            dt = datetime.fromisoformat(iso_str)
            meses = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
            fecha_str = f"{dt.day} de {meses[dt.month]}"
            mensaje += f"⚠️ Finaliza el {fecha_str}\n"
        except Exception:
            mensaje += f"⚠️ Finaliza el {product.fin_oferta[:10]}\n"
            
    return mensaje

def format_text_with_custom_emojis(text: str) -> dict:
    """
    Transforma un texto normal en uno compatible con 'Custom Emojis' de Telegram.
    Calcula exactamente en qué posición está cada emoji para decirle a Telegram 
    que lo reemplace por una versión animada o premium.
    """
    from src.integrations.telegram.emoji_mapper import CUSTOM_EMOJI_MAP
    
    entities = []
    
    # IMPORTANTE: Telegram no cuenta caracteres simples (1, 2, 3...), sino 'unidades UTF-16'. 
    # Algunos emojis ocupan más de una unidad, por lo que usamos encode('utf-16-le') 
    # para obtener el offset exacto que la API de Telegram requiere.
    
    for emoji_char, custom_id in CUSTOM_EMOJI_MAP.items():
        start = 0
        while True:
            # Buscamos dónde aparece el emoji en el texto
            idx = text.find(emoji_char, start)
            if idx == -1:
                break
                
            prefix = text[:idx]
            
            # Calculamos la posición real en el formato que entiende Telegram
            offset = len(prefix.encode('utf-16-le')) // 2
            length = len(emoji_char.encode('utf-16-le')) // 2
            
            entities.append({
                "type": "custom_emoji",
                "offset": offset,
                "length": length,
                "custom_emoji_id": custom_id
            })
            
            start = idx + len(emoji_char)

    # Añadimos una entidad para que TODO el mensaje aparezca en negrita
    total_length = len(text.encode('utf-16-le')) // 2
    entities.append({
        "type": "bold",
        "offset": 0,
        "length": total_length
    })

    return {
        "text": text,
        "entities": entities
    }
