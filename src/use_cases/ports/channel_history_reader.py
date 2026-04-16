from abc import ABC, abstractmethod
from typing import Iterable


class ChannelHistoryReader(ABC):
    @abstractmethod
    def iter_messages(self, channel_id: str, limit: int = None) -> Iterable[str]:
        raise NotImplementedError
