"""
Puerto de Repositorio de Categorías
Este archivo define la 'Interfaz' o contrato para guardar categorías. 
No dice CÓMO se guardan (eso lo hace el repositorio JSON), sino QUÉ 
métodos deben existir para que el sistema funcione correctamente.
"""

from abc import ABC, abstractmethod
from src.domain.category import CategoryCatalog

class CategoryRepository(ABC):
    """Interfaz abstracta para el almacenamiento de categorías."""
    
    @abstractmethod
    def load_catalog(self) -> CategoryCatalog:
        """Debe cargar y devolver el catálogo completo."""
        raise NotImplementedError

    @abstractmethod
    def save_catalog(self, catalog: CategoryCatalog) -> None:
        """Debe guardar el catálogo proporcionado."""
        raise NotImplementedError
