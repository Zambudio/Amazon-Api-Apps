"""
Caso de Uso: Obtener Categorías para la UI
Este archivo es una utilidad sencilla para la interfaz gráfica. 
Se encarga de leer el catálogo de categorías y devolverlas en una lista 
ordenada para que el usuario pueda seleccionarlas en el desplegable.
"""

from typing import List
from src.use_cases.ports.category_repository import CategoryRepository

class GetCategoriesForUIUseCase:
    """
    Simplemente carga el catálogo y devuelve los nombres de las categorías.
    """
    def __init__(self, category_repository: CategoryRepository):
        self.category_repository = category_repository

    def execute(self) -> List[str]:
        """Carga el catálogo y devuelve la lista de hashtags ordenada alfabéticamente."""
        catalog = self.category_repository.load_catalog()
        return catalog.to_sorted_list()
