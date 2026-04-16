import asyncio
from typing import Iterable

from src.use_cases.ports.channel_history_reader import ChannelHistoryReader


class TelegramHistoryReader(ChannelHistoryReader):
    """
    Lector de historial del canal usando una sesión de USUARIO.
    No usa Bot API porque esta no permite descargar histórico completo.
    """

    def __init__(self, api_id: str, api_hash: str, session_name: str = "telegram_user"):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name

    def iter_messages(self, channel_id: str, limit: int = None) -> Iterable[str]:
        try:
            from telethon import TelegramClient
            from telethon.tl.types import PeerChannel
        except ImportError as exc:
            raise RuntimeError(
                "Falta dependencia 'telethon'. Instala con: pip install telethon"
            ) from exc

        if not self.api_id or not self.api_hash:
            raise ValueError("Faltan TELEGRAM_USER_API_ID o TELEGRAM_USER_API_HASH.")

        async def _resolve_entity(client, raw_channel_id: str):
            raw = str(raw_channel_id).strip()
            # Soporta username/enlace público (ej: @canal, t.me/canal)
            if not raw or not raw.lstrip("-").isdigit():
                return await client.get_entity(raw)

            numeric = int(raw)
            # Formato típico de canales en Bot API: -1001234567890
            if raw.startswith("-100"):
                internal_channel_id = int(raw[4:])
                return await client.get_entity(PeerChannel(internal_channel_id))

            # Otros ids numéricos
            return await client.get_entity(numeric)

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
