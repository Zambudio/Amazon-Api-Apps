"""
Lector de Historial de Telegram (Usuario)
Este archivo permite leer los mensajes antiguos de un canal. A diferencia del 
Bot, que tiene limitaciones, este script usa una sesión de 'Usuario' para 
poder descargar y analizar publicaciones pasadas del canal.
"""

import asyncio
from typing import Iterable

from src.use_cases.ports.channel_history_reader import ChannelHistoryReader


class TelegramHistoryReader(ChannelHistoryReader):
    """
    Utiliza la librería Telethon para conectarse como si fuera una persona 
    real y así poder recorrer el histórico de mensajes del canal.
    """

    def __init__(self, api_id: str, api_hash: str, session_name: str = "telegram_user"):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name

    def iter_messages(self, channel_id: str, limit: int = None) -> Iterable[str]:
        """Recorre los mensajes del canal y devuelve su texto."""
        try:
            from telethon import TelegramClient
            from telethon.tl.types import PeerChannel
        except ImportError as exc:
            raise RuntimeError("Falta la librería 'telethon'.") from exc

        # Lógica interna para manejar diferentes tipos de IDs de canales
        async def _resolve_entity(client, raw_channel_id: str):
            raw = str(raw_channel_id).strip()
            if not raw or not raw.lstrip("-").isdigit():
                return await client.get_entity(raw)

            numeric = int(raw)
            if raw.startswith("-100"):
                internal_channel_id = int(raw[4:])
                return await client.get_entity(PeerChannel(internal_channel_id))
            return await client.get_entity(numeric)

        # Función asíncrona para descargar los mensajes
        async def _collect_messages():
            texts = []
            async with TelegramClient(self.session_name, int(self.api_id), self.api_hash) as client:
                entity = await _resolve_entity(client, channel_id)
                async for message in client.iter_messages(entity, limit=limit):
                    text = message.message or ""
                    if text:
                        texts.append(text)
            return texts

        for text in asyncio.run(_collect_messages()):
            yield text
