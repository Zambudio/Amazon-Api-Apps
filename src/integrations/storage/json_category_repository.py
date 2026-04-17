import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.domain.category import CategoryCatalog
from src.use_cases.ports.category_repository import CategoryRepository


class JsonCategoryRepository(CategoryRepository):
    def __init__(self, file_path: str):
        self.file_path = file_path

    def _get_writable_catalog_path(self) -> Path:
        path = Path(self.file_path)
        if getattr(sys, "frozen", False):
            exe_dir = Path(sys.executable).resolve().parent
            writable_dir = exe_dir / path.parent
            writable_dir.mkdir(parents=True, exist_ok=True)
            return writable_dir / path.name
        return path

    def _load_from_bundle(self) -> CategoryCatalog:
        if not getattr(sys, "frozen", False):
            return CategoryCatalog()

        meipass = getattr(sys, "_MEIPASS", None)
        if not meipass:
            return CategoryCatalog()

        bundle_path = Path(meipass) / "data" / Path(self.file_path).name
        if not bundle_path.exists():
            return CategoryCatalog()

        try:
            with open(bundle_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except (json.JSONDecodeError, OSError):
            return CategoryCatalog()

        return CategoryCatalog.from_iterable(payload.get("categories", []))

    def load_catalog(self) -> CategoryCatalog:
        path = Path(self.file_path)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
            except (json.JSONDecodeError, OSError):
                return CategoryCatalog()

            categories = payload.get("categories", [])
            return CategoryCatalog.from_iterable(categories)

        return self._load_from_bundle()

    def save_catalog(self, catalog: CategoryCatalog) -> None:
        writable_path = self._get_writable_catalog_path()
        directory = writable_path.parent
        if directory:
            os.makedirs(directory, exist_ok=True)

        payload = {
            "version": 1,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "categories": catalog.to_sorted_list(),
        }
        tmp_path = directory / f"{writable_path.name}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=True, indent=2)

        os.replace(tmp_path, writable_path)
