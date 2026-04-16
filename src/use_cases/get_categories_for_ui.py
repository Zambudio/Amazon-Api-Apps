from typing import List

from src.use_cases.ports.category_repository import CategoryRepository


class GetCategoriesForUIUseCase:
    def __init__(self, category_repository: CategoryRepository):
        self.category_repository = category_repository

    def execute(self) -> List[str]:
        catalog = self.category_repository.load_catalog()
        return catalog.to_sorted_list()
