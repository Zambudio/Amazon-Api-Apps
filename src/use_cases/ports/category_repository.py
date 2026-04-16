from abc import ABC, abstractmethod

from src.domain.category import CategoryCatalog


class CategoryRepository(ABC):
    @abstractmethod
    def load_catalog(self) -> CategoryCatalog:
        raise NotImplementedError

    @abstractmethod
    def save_catalog(self, catalog: CategoryCatalog) -> None:
        raise NotImplementedError
