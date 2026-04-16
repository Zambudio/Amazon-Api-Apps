import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.config.settings import Config
from src.integrations.storage.json_category_repository import JsonCategoryRepository
from src.integrations.telegram.telegram_history_reader import TelegramHistoryReader
from src.use_cases.build_category_catalog_from_channel import BuildCategoryCatalogFromChannelUseCase


def resolve_channel(target: str) -> str:
    if target == "main":
        return Config.TELEGRAM_MAIN_CHANNEL_ID
    if target == "admin":
        return Config.TELEGRAM_ADMIN_CHANNEL_ID
    return target


def main():
    parser = argparse.ArgumentParser(description="Sincroniza hashtags del histórico de Telegram.")
    parser.add_argument("--channel", default="main", help="main | admin | id del canal")
    parser.add_argument("--limit", type=int, default=None, help="Límite de mensajes a leer")
    parser.add_argument("--dry-run", action="store_true", help="No persiste cambios")
    args = parser.parse_args()

    channel_id = resolve_channel(args.channel)
    if not channel_id:
        print("Error: No se pudo resolver el canal destino.")
        sys.exit(1)

    repository = JsonCategoryRepository(Config.CATEGORIES_FILE_PATH)
    history_reader = TelegramHistoryReader(
        api_id=Config.TELEGRAM_USER_API_ID,
        api_hash=Config.TELEGRAM_USER_API_HASH,
        session_name=Config.TELEGRAM_USER_SESSION,
    )

    use_case = BuildCategoryCatalogFromChannelUseCase(
        category_repository=repository,
        history_reader=history_reader,
    )

    result = use_case.execute(channel_id=channel_id, limit=args.limit, persist=not args.dry_run)

    print("Sincronización completada:")
    print(f"- Mensajes procesados: {result['processed_messages']}")
    print(f"- Categorías nuevas: {result['new_categories']}")
    print(f"- Categorías totales: {result['total_categories']}")
    print(f"- Archivo catálogo: {Config.CATEGORIES_FILE_PATH}")


if __name__ == "__main__":
    main()
