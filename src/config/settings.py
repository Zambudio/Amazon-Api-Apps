import os
import sys
from pathlib import Path
from typing import Optional


def _get_app_base_dir() -> Path:
    """
    Devuelve la raíz de ejecución:
    - Script: raíz del proyecto
    - Ejecutable PyInstaller: carpeta del ejecutable o el directorio interno del bundle
    """
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        if hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS)

        internal_dir = exe_dir / "_internal"
        if internal_dir.exists():
            return internal_dir

        return exe_dir
    return Path(__file__).resolve().parents[2]


def _resolve_runtime_path(value: str, default_relative: str) -> str:
    base_dir = _get_app_base_dir()
    project_root = Path(__file__).resolve().parents[2]
    raw = (value or "").strip()
    relative = Path(raw) if raw else Path(default_relative)

    if relative.is_absolute():
        return str(relative)

    search_bases = [
        base_dir,
        Path.cwd(),
        project_root,
        base_dir.parent,
    ]

    # Priorizamos el primer archivo existente para evitar catálogos "vacíos"
    # cuando cambia el cwd entre script y ejecutable.
    for base in search_bases:
        candidate = (base / relative).resolve()
        if candidate.exists():
            return str(candidate)

    return str((base_dir / relative).resolve())

def _resolve_data_path(value: str, default_relative: str) -> str:
    raw = (value or "").strip()
    if raw:
        return _resolve_runtime_path(raw, default_relative)

    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        return str((exe_dir / default_relative).resolve())

    return _resolve_runtime_path(raw, default_relative)


def load_config():
    try:
        from dotenv import load_dotenv

        base_dir = _get_app_base_dir()
        exe_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else None
        search_paths = [
            base_dir / ".env",
            base_dir.parent / ".env",
        ]

        if exe_dir is not None:
            search_paths.extend([
                exe_dir / ".env",
                Path.cwd() / ".env",
            ])

        for env_path in search_paths:
            if env_path.exists():
                load_dotenv(dotenv_path=env_path)
                return

        load_dotenv()
    except ImportError:
        pass

# Ejecutamos al importar
load_config()

class Config:
    # Amazon API Config
    AMAZON_CLIENT_ID: str = os.getenv("AMAZON_CLIENT_ID", "")
    AMAZON_CLIENT_SECRET: str = os.getenv("AMAZON_CLIENT_SECRET", "")
    AMAZON_AFFILIATE_TAG: str = os.getenv("AMAZON_AFFILIATE_TAG", "buenchollo0b-21")
    
    # Telegram Config
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_ADMIN_CHANNEL_ID: str = os.getenv("TELEGRAM_ADMIN_CHANNEL_ID", os.getenv("TELEGRAM_CHANNEL_ID", ""))
    TELEGRAM_MAIN_CHANNEL_ID: str = os.getenv("TELEGRAM_MAIN_CHANNEL_ID", "")
    TELEGRAM_USER_API_ID: str = os.getenv("TELEGRAM_USER_API_ID", "")
    TELEGRAM_USER_API_HASH: str = os.getenv("TELEGRAM_USER_API_HASH", "")
    TELEGRAM_USER_SESSION: str = _resolve_runtime_path(
        os.getenv("TELEGRAM_USER_SESSION", ""),
        "runtime/telegram_user"
    )
    
    # OpenAI Config para copys atractivos
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Categorías/hashtags
    CATEGORIES_FILE_PATH: str = _resolve_data_path(
        os.getenv("CATEGORIES_FILE_PATH", ""),
        "data/categories.json"
    )
