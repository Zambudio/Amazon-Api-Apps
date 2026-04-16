import json
import os
from datetime import datetime, timezone

from src.domain.category import CategoryCatalog
from src.use_cases.ports.category_repository import CategoryRepository


class JsonCategoryRepository(CategoryRepository):
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load_catalog(self) -> CategoryCatalog:
        if not os.path.exists(self.file_path):
            return CategoryCatalog()

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except (json.JSONDecodeError, OSError):
            return CategoryCatalog()

        categories = payload.get("categories", [])
        return CategoryCatalog.from_iterable(categories)

    def save_catalog(self, catalog: CategoryCatalog) -> None:
        directory = os.path.dirname(self.file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        payload = {
            "version": 1,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "categories": catalog.to_sorted_list(),
        }
        tmp_path = f"{self.file_path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=True, indent=2)

        os.replace(tmp_path, self.file_path)
