"""
Configuración General del Sistema
Este archivo gestiona todas las variables de entorno, claves de API y rutas de archivos. 
Centraliza la configuración para que el resto del programa sepa dónde encontrar datos 
y cómo conectarse a servicios externos como Amazon o Telegram.
"""

import os
import sys
from pathlib import Path
from typing import Optional


def _get_app_base_dir() -> Path:
    """
    Determina la carpeta raíz donde reside la aplicación. 
    Es vital para que el programa funcione tanto si se ejecuta como código (.py) 
    o como un archivo ejecutable (.exe) compilado con PyInstaller.
    """
    if getattr(sys, "frozen", False):
        # Si estamos en un ejecutable .exe
        exe_dir = Path(sys.executable).resolve().parent
        if hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS)

        internal_dir = exe_dir / "_internal"
        if internal_dir.exists():
            return internal_dir

        return exe_dir
    # Si estamos ejecutando el script .py directamente
    return Path(__file__).resolve().parents[2]


def _resolve_runtime_path(value: str, default_relative: str) -> str:
    """
    Resuelve una ruta de archivo para que sea válida en tiempo de ejecución.
    Busca el archivo en varias carpetas posibles para asegurar que se encuentre 
    incluso si el directorio de trabajo cambia.
    """
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

    # Priorizamos el primer archivo existente para evitar errores al mover la aplicación.
    for base in search_bases:
        candidate = (base / relative).resolve()
        if candidate.exists():
            return str(candidate)

    return str((base_dir / relative).resolve())

def _resolve_data_path(value: str, default_relative: str) -> str:
    """
    Similar a resolve_runtime_path pero optimizado para archivos de datos (JSON, etc.)
    que suelen estar en la carpeta 'data/'.
    """
    raw = (value or "").strip()
    if raw:
        return _resolve_runtime_path(raw, default_relative)

    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        return str((exe_dir / default_relative).resolve())

    return _resolve_runtime_path(raw, default_relative)


def load_config():
    """
    Carga las variables de entorno desde el archivo .env.
    Busca el archivo en múltiples ubicaciones comunes.
    """
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

# Ejecutamos la carga de configuración al importar este módulo
load_config()

class Config:
    """
    Clase contenedora de todas las constantes y configuraciones del proyecto.
    """
    # Configuración de la API de Amazon (Credenciales para obtener productos)
    AMAZON_CLIENT_ID: str = os.getenv("AMAZON_CLIENT_ID", "")
    AMAZON_CLIENT_SECRET: str = os.getenv("AMAZON_CLIENT_SECRET", "")
    AMAZON_AFFILIATE_TAG: str = os.getenv("AMAZON_AFFILIATE_TAG", "buenchollo0b-21")
    
    # Configuración de Telegram (Tokens para enviar mensajes y leer canales)
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_ADMIN_CHANNEL_ID: str = os.getenv("TELEGRAM_ADMIN_CHANNEL_ID", os.getenv("TELEGRAM_CHANNEL_ID", ""))
    TELEGRAM_MAIN_CHANNEL_ID: str = os.getenv("TELEGRAM_MAIN_CHANNEL_ID", "")
    TELEGRAM_USER_API_ID: str = os.getenv("TELEGRAM_USER_API_ID", "")
    TELEGRAM_USER_API_HASH: str = os.getenv("TELEGRAM_USER_API_HASH", "")
    TELEGRAM_USER_SESSION: str = _resolve_runtime_path(
        os.getenv("TELEGRAM_USER_SESSION", ""),
        "runtime/telegram_user"
    )
    
    # Configuración de OpenAI para la generación de textos creativos
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Rutas a archivos locales de almacenamiento
    CATEGORIES_FILE_PATH: str = _resolve_data_path(
        os.getenv("CATEGORIES_FILE_PATH", ""),
        "data/categories.json"
    )
