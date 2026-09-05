"""
Herramienta CLI: Migrar Categorías
Este script se encarga de estandarizar todas las categorías existentes al 
formato actual (inicial en mayúscula). Es una herramienta de mantenimiento 
para asegurar que el catálogo de hashtags sea coherente y visualmente limpio.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.config.settings import Config
from src.integrations.storage.json_category_repository import JsonCategoryRepository


def read_raw_categories(file_path: str):
    """Lee el archivo JSON de categorías de forma bruta para comparar cambios."""
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
            return payload.get("categories", [])
    except Exception:
        return []


def main():
    parser = argparse.ArgumentParser(
        description="Migra categorías al formato canónico actual (inicial mayúscula)."
    )
    parser.add_argument("--dry-run", action="store_true", help="Muestra los cambios sin guardarlos.")
    args = parser.parse_args()

    file_path = Config.CATEGORIES_FILE_PATH
    before_raw = read_raw_categories(file_path)

    # El repositorio normaliza automáticamente al cargar/guardar
    repository = JsonCategoryRepository(file_path)
    catalog = repository.load_catalog()
    after = catalog.to_sorted_list()

    before_unique = sorted(set(before_raw))
    removed_or_changed = sorted(set(before_unique) - set(after))
    added_or_changed = sorted(set(after) - set(before_unique))

    print("Resultado de la migración de categorías:")
    print(f"- Archivo procesado: {file_path}")
    print(f"- Entradas antes: {len(before_unique)}")
    print(f"- Entradas después: {len(after)}")

    if removed_or_changed:
        print("\nEntradas que han sido modificadas o eliminadas:")
        for tag in removed_or_changed[:20]:
            print(f"  - {tag}")

    if added_or_changed:
        print("\nNuevas entradas normalizadas:")
        for tag in added_or_changed[:20]:
            print(f"  + {tag}")

    if args.dry_run:
        print("\nModo de prueba (dry-run): No se han guardado los cambios.")
        return

    # Guardamos el catálogo ya normalizado
    repository.save_catalog(catalog)
    print("\nMigración completada con éxito.")


if __name__ == "__main__":
    main()
