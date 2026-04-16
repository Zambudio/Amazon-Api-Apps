from dataclasses import dataclass, field
from typing import Iterable, List, Set

from src.domain.hashtag_rules import normalize_hashtag


@dataclass(frozen=True)
class Category:
    name: str

    @staticmethod
    def from_raw(tag: str) -> "Category":
        normalized = normalize_hashtag(tag)
        if not normalized:
            raise ValueError("Categoría inválida")
        return Category(name=normalized)


@dataclass
class CategoryCatalog:
    categories: Set[str] = field(default_factory=set)

    @staticmethod
    def from_iterable(values: Iterable[str]) -> "CategoryCatalog":
        catalog = CategoryCatalog()
        catalog.add_many(values)
        return catalog

    def add(self, tag: str) -> bool:
        normalized = normalize_hashtag(tag)
        if not normalized:
            return False
        before = len(self.categories)
        self.categories.add(normalized)
        return len(self.categories) > before

    def add_many(self, tags: Iterable[str]) -> int:
        added = 0
        for tag in tags:
            if self.add(tag):
                added += 1
        return added

    def to_sorted_list(self) -> List[str]:
        return sorted(self.categories)
