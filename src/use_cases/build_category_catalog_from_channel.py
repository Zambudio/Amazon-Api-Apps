from src.domain.hashtag_rules import extract_hashtags
from src.use_cases.ports.category_repository import CategoryRepository
from src.use_cases.ports.channel_history_reader import ChannelHistoryReader


class BuildCategoryCatalogFromChannelUseCase:
    def __init__(self, category_repository: CategoryRepository, history_reader: ChannelHistoryReader):
        self.category_repository = category_repository
        self.history_reader = history_reader

    def execute(self, channel_id: str, limit: int = None, persist: bool = True) -> dict:
        catalog = self.category_repository.load_catalog()

        total_messages = 0
        added = 0

        for text in self.history_reader.iter_messages(channel_id=channel_id, limit=limit):
            total_messages += 1
            tags = extract_hashtags(text)
            added += catalog.add_many(tags)

        if persist:
            self.category_repository.save_catalog(catalog)
        return {
            "processed_messages": total_messages,
            "new_categories": added,
            "total_categories": len(catalog.categories),
        }
