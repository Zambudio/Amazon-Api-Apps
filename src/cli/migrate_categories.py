import argparse
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.config.settings import Config
from src.integrations.storage.json_category_repository import JsonCategoryRepository


def read_raw_categories(file_path: str):
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
            return payload.get("categories", [])
    except (json.JSONDecodeError, OSError):
        return []


def main():
    parser = argparse.ArgumentParser(
        description="Migra categorías al formato canónico actual (inicial mayúscula)."
    )
    parser.add_argument("--dry-run", action="store_true", help="Muestra cambios sin guardar")
    args = parser.parse_args()

    file_path = Config.CATEGORIES_FILE_PATH
    before_raw = read_raw_categories(file_path)

    repository = JsonCategoryRepository(file_path)
    catalog = repository.load_catalog()
    after = catalog.to_sorted_list()

    before_unique = sorted(set(before_raw))
    removed_or_changed = sorted(set(before_unique) - set(after))
    added_or_changed = sorted(set(after) - set(before_unique))

    print("Resultado migración categorías:")
    print(f"- Archivo: {file_path}")
    print(f"- Antes (únicas): {len(before_unique)}")
    print(f"- Después (únicas): {len(after)}")
    print(f"- Cambios detectados: {len(removed_or_changed) + len(added_or_changed)}")

    if removed_or_changed:
        print("\nEntradas antiguas (reemplazadas/eliminadas):")
        for tag in removed_or_changed[:50]:
            print(f"  - {tag}")
        if len(removed_or_changed) > 50:
            print(f"  ... y {len(removed_or_changed) - 50} más")

    if added_or_changed:
        print("\nEntradas nuevas normalizadas:")
        for tag in added_or_changed[:50]:
            print(f"  + {tag}")
        if len(added_or_changed) > 50:
            print(f"  ... y {len(added_or_changed) - 50} más")

    if args.dry_run:
        print("\nDry-run: no se ha guardado ningún cambio.")
        return

    repository.save_catalog(catalog)
    print("\nMigración aplicada y guardada.")


if __name__ == "__main__":
    main()
