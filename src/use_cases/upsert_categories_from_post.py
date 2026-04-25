"""
Caso de Uso: Actualizar Catálogo desde Post
Este archivo permite añadir nuevas categorías al catálogo a medida que se 
publican posts. Si el usuario escribe un nuevo hashtag manualmente, este 
caso de uso lo detecta y lo guarda permanentemente en el sistema.
"""

from src.domain.hashtag_rules import extract_hashtags, normalize_hashtag
from src.use_cases.ports.category_repository import CategoryRepository


class UpsertCategoriesFromPostUseCase:
    """
    Gestiona la actualización inteligente del catálogo tras crear un post.
    """
    def __init__(self, category_repository: CategoryRepository):
        self.category_repository = category_repository

    def execute(self, post_text: str, manual_category: str = "") -> dict:
        """Detecta nuevos hashtags en el texto o en la entrada manual y los guarda."""
        catalog = self.category_repository.load_catalog()
        added = 0

        # Si el usuario escribió una categoría nueva en el cuadro de texto manual
        if manual_category:
            if catalog.add(normalize_hashtag(manual_category)):
                added += 1

        # También escaneamos el texto del mensaje final por si hay más hashtags
        hashtags = extract_hashtags(post_text)
        added += catalog.add_many(hashtags)

        # Guardamos los cambios
        self.category_repository.save_catalog(catalog)
        return {
            "added": added,
            "total": len(catalog.categories),
        }
