
import asyncio
import json
import re
import os
import requests
from telethon import TelegramClient
from telethon.tl.types import PeerChannel
from src.config.settings import Config

# Cache para no expandir el mismo link varias veces
link_cache = {}

def get_amazon_asin(url):
    if not url: return None
    patterns = [r'/dp/([A-Z0-9]{10})', r'/gp/product/([A-Z0-9]{10})', r'ASIN=([A-Z0-9]{10})']
    for pattern in patterns:
        match = re.search(pattern, url)
        if match: return match.group(1)
    return None

def expand_url(url):
    if not url: return None, None
    if url in link_cache: return link_cache[url]
    try:
        if "amzn.to" in url or "bit.ly" in url or "t.me" in url:
            res = requests.head(url, allow_redirects=True, timeout=5)
            final_url = res.url
            asin = get_amazon_asin(final_url)
            link_cache[url] = (final_url, asin)
            return final_url, asin
    except Exception: pass
    return url, get_amazon_asin(url)

async def extract_data():
    api_id = Config.TELEGRAM_USER_API_ID
    api_hash = Config.TELEGRAM_USER_API_HASH
    # Probamos con el Main Channel ID si existe, sino el Admin
    channel_id = Config.TELEGRAM_MAIN_CHANNEL_ID or Config.TELEGRAM_ADMIN_CHANNEL_ID
    session_path = "telegram_user"

    print(f"Conectando a Telegram para leer el canal: {channel_id}...")
    
    products = []
    msg_count = 0

    async with TelegramClient(session_path, int(api_id), api_hash) as client:
        try:
            raw = str(channel_id).strip()
            if raw.lstrip("-").isdigit():
                if raw.startswith("-100"):
                    entity = await client.get_entity(PeerChannel(int(raw[4:])))
                else:
                    entity = await client.get_entity(int(raw))
            else:
                entity = await client.get_entity(raw)
        except Exception as e:
            print(f"Error al acceder al canal: {e}")
            return

        print("Iniciando descarga de historial completo...")
        async for message in client.iter_messages(entity):
            msg_count += 1
            if not message.message:
                continue

            text = message.message
            
            # Buscamos si hay un link de tienda, si no hay link, no es un anuncio de producto
            link_match = re.search(r'(https?://(?:amzn\.to|www\.amazon\.es|pccomponentes\.com|bit\.ly|t\.me)[^\s\n\r]+)', text)
            if not link_match:
                continue

            affiliate_link = link_match.group(1).strip().rstrip('.,✏️')
            
            # Título: Primera línea o primera frase con sentido
            lines = text.split('\n')
            title = lines[0].replace('🍄', '').replace('🔥', '').replace('📍', '').strip()
            if not title and len(lines) > 1:
                title = lines[1].strip()

            # Descripción: Intentamos capturar todo lo que parezca descripción
            description = ""
            if '✏️' in text:
                description = text.split('✏️')[1].split('⚠️')[0].split('#')[0].strip()
            elif len(lines) > 2:
                # Si no hay icono de lápiz, cogemos lo que haya entre el título/precio y el link
                description = " ".join(lines[1:-1]).strip()

            # Precios
            current_price = None
            previous_price = None
            price_match = re.search(r'(?:Precio|Oferta):\s*([\d,.]+)\s*€(?:\s*\(antes\s*([\d,.]+)\s*€\))?', text, re.I)
            if price_match:
                def p(s):
                    if not s: return None
                    s = s.replace('.', '') if ',' in s else s
                    return float(s.replace(',', '.'))
                current_price = p(price_match.group(1))
                previous_price = p(price_match.group(2))

            # Imagen y ASIN
            final_url, asin = expand_url(affiliate_link)
            image_url = None
            if asin:
                image_url = f"https://images-na.ssl-images-amazon.com/images/P/{asin}.01._SCLZZZZZZZ_.jpg"
            elif message.media and hasattr(message.media, 'webpage') and message.media.webpage:
                if hasattr(message.media.webpage, 'photo') and message.media.webpage.photo:
                    image_url = "Imagen de preview disponible"
            
            # Marca
            words = title.split()
            brand = words[0].strip(',"()') if words else "Desconocida"

            products.append({
                "id": message.id,
                "fecha": message.date.isoformat(),
                "titulo": title,
                "marca": brand,
                "precio_actual": current_price,
                "precio_antes": previous_price,
                "descripcion": description,
                "enlace": affiliate_link,
                "url_imagen": image_url,
                "categoria": (re.findall(r'#(\w+)', text) or ["General"])[0]
            })

            if len(products) % 50 == 0:
                print(f"Extraídos {len(products)} productos de {msg_count} mensajes analizados...")

    with open('todos_los_productos.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=4)
    
    print(f"\n¡Finalizado! Se han leído {msg_count} mensajes y extraído {len(products)} productos.")
    print("Guardado en todos_los_productos.json")

if __name__ == "__main__":
    asyncio.run(extract_data())
