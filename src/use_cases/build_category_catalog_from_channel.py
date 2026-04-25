"""
Caso de Uso: Construir Catálogo desde Canal
Este archivo permite "aprender" de un canal de Telegram ya existente. 
Lee los mensajes antiguos, extrae los hashtags que se han usado y los 
guarda en nuestro catálogo local para poder usarlos en el futuro.
"""

from src.domain.hashtag_rules import extract_hashtags
from src.use_cases.ports.category_repository import CategoryRepository
from src.use_cases.ports.channel_history_reader import ChannelHistoryReader


class BuildCategoryCatalogFromChannelUseCase:
    """
    Orquesta la lectura del historial y la actualización del repositorio de categorías.
    """
    def __init__(self, category_repository: CategoryRepository, history_reader: ChannelHistoryReader):
        self.category_repository = category_repository
        self.history_reader = history_reader

    def execute(self, channel_id: str, limit: int = None, persist: bool = True) -> dict:
        """Recorre el canal extrayendo categorías nuevas."""
        catalog = self.category_repository.load_catalog()
        total_messages = 0
        added = 0

        # Leemos los mensajes uno a uno
        for text in self.history_reader.iter_messages(channel_id=channel_id, limit=limit):
            total_messages += 1
            # Extraemos los hashtags (#Cosas) del texto del mensaje
            tags = extract_hashtags(text)
            # Los añadimos al catálogo (evita duplicados automáticamente)
            added += catalog.add_many(tags)

        # Guardamos el catálogo actualizado en el disco
        if persist:
            self.category_repository.save_catalog(catalog)
            
        return {
            "processed_messages": total_messages,
            "new_categories": added,
            "total_categories": len(catalog.categories),
        }
