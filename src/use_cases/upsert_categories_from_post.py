from src.domain.hashtag_rules import extract_hashtags, normalize_hashtag
from src.use_cases.ports.category_repository import CategoryRepository


class UpsertCategoriesFromPostUseCase:
    def __init__(self, category_repository: CategoryRepository):
        self.category_repository = category_repository

    def execute(self, post_text: str, manual_category: str = "") -> dict:
        catalog = self.category_repository.load_catalog()
        added = 0

        if manual_category:
            if catalog.add(normalize_hashtag(manual_category)):
                added += 1

        hashtags = extract_hashtags(post_text)
        added += catalog.add_many(hashtags)

        self.category_repository.save_catalog(catalog)
        return {
            "added": added,
            "total": len(catalog.categories),
        }
