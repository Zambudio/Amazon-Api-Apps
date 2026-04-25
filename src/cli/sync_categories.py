"""
Herramienta CLI: Sincronizar Categorías
Este script permite leer el historial de un canal de Telegram y añadir 
automáticamente los hashtags encontrados al catálogo local. Es útil para 
mantener el catálogo sincronizado con lo que se publica en el canal real.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.config.settings import Config
from src.integrations.storage.json_category_repository import JsonCategoryRepository
from src.integrations.telegram.telegram_history_reader import TelegramHistoryReader
from src.use_cases.build_category_catalog_from_channel import BuildCategoryCatalogFromChannelUseCase


def resolve_channel(target: str) -> str:
    """Convierte alias como 'main' o 'admin' en sus IDs reales de Telegram."""
    if target == "main":
        return Config.TELEGRAM_MAIN_CHANNEL_ID
    if target == "admin":
        return Config.TELEGRAM_ADMIN_CHANNEL_ID
    return target


def main():
    parser = argparse.ArgumentParser(description="Sincroniza hashtags del histórico de Telegram.")
    parser.add_argument("--channel", default="main", help="main | admin | id_directo_del_canal")
    parser.add_argument("--limit", type=int, default=None, help="Máximo de mensajes a leer.")
    parser.add_argument("--dry-run", action="store_true", help="No guarda los cambios en el disco.")
    args = parser.parse_args()

    channel_id = resolve_channel(args.channel)
    if not channel_id:
        print("Error: No se ha podido identificar el canal destino.")
        sys.exit(1)

    # Preparamos las herramientas necesarias para la sincronización
    repository = JsonCategoryRepository(Config.CATEGORIES_FILE_PATH)
    history_reader = TelegramHistoryReader(
        api_id=Config.TELEGRAM_USER_API_ID,
        api_hash=Config.TELEGRAM_USER_API_HASH,
        session_name=Config.TELEGRAM_USER_SESSION,
    )

    # Ejecutamos el proceso de sincronización
    use_case = BuildCategoryCatalogFromChannelUseCase(
        category_repository=repository,
        history_reader=history_reader,
    )

    result = use_case.execute(channel_id=channel_id, limit=args.limit, persist=not args.dry_run)

    print("Sincronización finalizada:")
    print(f"- Mensajes analizados: {result['processed_messages']}")
    print(f"- Nuevas categorías encontradas: {result['new_categories']}")
    print(f"- Total de categorías en el catálogo: {result['total_categories']}")


if __name__ == "__main__":
    main()
