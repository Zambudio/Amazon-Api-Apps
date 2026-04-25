"""
Puerto de Lector de Historial
Este archivo define el contrato para leer mensajes de un canal. 
Permite que el sistema pueda usar diferentes formas de leer el historial 
(por ejemplo, Telethon o una API futura) sin cambiar el código principal.
"""

from abc import ABC, abstractmethod
from typing import Iterable

class ChannelHistoryReader(ABC):
    """Interfaz abstracta para leer mensajes de un canal de Telegram."""
    
    @abstractmethod
    def iter_messages(self, channel_id: str, limit: int = None) -> Iterable[str]:
        """Debe devolver un generador que recorra los textos de los mensajes del canal."""
        raise NotImplementedError
