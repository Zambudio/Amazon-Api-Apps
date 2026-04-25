"""
Script: Extraer Datos del Canal
Este script se conecta a un canal de Telegram y descarga todos los mensajes 
pasados para crear un archivo JSON con los productos que ya se han publicado. 
Es útil para migrar datos o analizar la competencia.
"""

import asyncio
import json
import re
import os
import requests
from telethon import TelegramClient
from telethon.tl.types import PeerChannel
from src.config.settings import Config

# Diccionario para recordar enlaces ya procesados y no repetir trabajo
link_cache = {}

def get_amazon_asin(url):
    """Extrae el código ASIN de un enlace de Amazon."""
    if not url: return None
    patterns = [r'/dp/([A-Z0-9]{10})', r'/gp/product/([A-Z0-9]{10})', r'ASIN=([A-Z0-9]{10})']
    for pattern in patterns:
        match = re.search(pattern, url)
        if match: return match.group(1)
    return None

def expand_url(url):
    """Sigue las redirecciones de enlaces cortos (bit.ly, amzn.to) para obtener la URL real."""
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
    """Función principal que descarga y procesa los mensajes del canal."""
    api_id = Config.TELEGRAM_USER_API_ID
    api_hash = Config.TELEGRAM_USER_API_HASH
    channel_id = Config.TELEGRAM_MAIN_CHANNEL_ID or Config.TELEGRAM_ADMIN_CHANNEL_ID
    session_path = "telegram_user"

    print(f"Conectando a Telegram para leer el canal: {channel_id}...")
    
    products = []
    msg_count = 0

    async with TelegramClient(session_path, int(api_id), api_hash) as client:
        try:
            # Resolvemos el ID del canal para que Telethon lo entienda
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

        print("Iniciando descarga de historial...")
        async for message in client.iter_messages(entity):
            msg_count += 1
            if not message.message: continue
            text = message.message
            
            # Buscamos enlaces de tiendas en el texto
            link_match = re.search(r'(https?://(?:amzn\.to|www\.amazon\.es|pccomponentes\.com|bit\.ly|t\.me)[^\s\n\r]+)', text)
            if not link_match: continue

            affiliate_link = link_match.group(1).strip().rstrip('.,✏️')
            
            # Limpiamos el título y extraemos precios y descripción básica
            lines = text.split('\n')
            title = lines[0].replace('🍄', '').replace('🔥', '').replace('📍', '').strip()
            
            # Guardamos la información del producto extraída del mensaje
            final_url, asin = expand_url(affiliate_link)
            image_url = f"https://images-na.ssl-images-amazon.com/images/P/{asin}.01._SCLZZZZZZZ_.jpg" if asin else None

            products.append({
                "id": message.id,
                "fecha": message.date.isoformat(),
                "titulo": title,
                "enlace": affiliate_link,
                "url_imagen": image_url,
                "categoria": (re.findall(r'#(\w+)', text) or ["General"])[0]
            })

    # Guardamos todo en un archivo JSON para su posterior uso
    with open('todos_los_productos.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=4)
    
    print(f"Finalizado. Extraídos {len(products)} productos.")

if __name__ == "__main__":
    asyncio.run(extract_data())
