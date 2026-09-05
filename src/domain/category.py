"""
Gestión de Categorías
Este archivo define cómo se comportan las categorías (hashtags) en el sistema. 
Permite crear categorías individuales y catálogos completos, asegurando que 
siempre tengan un formato correcto y estén ordenadas.
"""

from dataclasses import dataclass, field
from typing import Iterable, List, Set

from src.domain.hashtag_rules import normalize_hashtag


@dataclass(frozen=True)
class Category:
    """
    Representa una categoría única (ej: #Hogar).
    Se asegura de que el nombre esté normalizado al crearse.
    """
    name: str

    @staticmethod
    def from_raw(tag: str) -> "Category":
        normalized = normalize_hashtag(tag)
        if not normalized:
            raise ValueError("Categoría inválida")
        return Category(name=normalized)


@dataclass
class CategoryCatalog:
    """
    Un contenedor para muchas categorías. 
    Evita duplicados y permite añadir categorías de forma masiva.
    """
    categories: Set[str] = field(default_factory=set)

    @staticmethod
    def from_iterable(values: Iterable[str]) -> "CategoryCatalog":
        catalog = CategoryCatalog()
        catalog.add_many(values)
        return catalog

    def add(self, tag: str) -> bool:
        """Añade una categoría tras normalizarla. Retorna True si se añadió (no existía)."""
        normalized = normalize_hashtag(tag)
        if not normalized:
            return False
        before = len(self.categories)
        self.categories.add(normalized)
        return len(self.categories) > before

    def add_many(self, tags: Iterable[str]) -> int:
        """Añade múltiples categorías y devuelve cuántas se añadieron realmente."""
        added = 0
        for tag in tags:
            if self.add(tag):
                added += 1
        return added

    def to_sorted_list(self) -> List[str]:
        """Devuelve la lista de categorías ordenada alfabéticamente."""
        return sorted(self.categories)
