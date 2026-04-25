# 🚀 Publicador BuenChollo - Amazon to Telegram Automation

Este proyecto es una herramienta integral para la gestión, enriquecimiento y publicación automatizada de ofertas de Amazon en canales de Telegram. Combina una interfaz gráfica (GUI) para Windows con un "Cerebro Servidor" (FastAPI) diseñado para ejecutarse en un NAS (Synology) y gestionar publicaciones programadas.

## 🏗️ Arquitectura del Sistema

El proyecto sigue una arquitectura de capas (Clean Architecture simplificada):

1.  **Interfaz (UI):** 
    - `src/ui/main_gui.py`: Aplicación de escritorio moderna construida con `tkinter` y `ttkbootstrap`.
    - `run_gui.py`: Punto de entrada para ejecutar la interfaz.
2.  **Servidor (Backend):**
    - `src/server/nas_api.py`: API REST con FastAPI para la programación y ejecución autónoma de posts desde un servidor/NAS.
3.  **Casos de Uso:**
    - `src/use_cases/generate_post.py`: Orquesta la extracción de datos, síntesis con IA y formateo del mensaje.
4.  **Servicios e Integraciones:**
    - `AmazonService` / `amazon_api.py`: Integración con Amazon Creators API v3.2.
    - `GPTService`: Uso de OpenAI para resumir descripciones y categorizar productos.
    - `PublisherService`: Lógica central de envío a Telegram (Soporta múltiples canales y emojis premium).
5.  **Dominio y Persistencia:**
    - `src/domain/entities.py`: Modelos de datos (ProductInfo, etc.).
    - `src/integrations/storage/`: Repositorio JSON para el catálogo de categorías y hashtags.

## 🛠️ Tecnologías Principales

- **Lenguaje:** Python 3.11+
- **GUI:** `tkinter`, `ttkbootstrap` (Tema Darkly), `Pillow` (Gestión de imágenes).
- **Web/API:** `FastAPI`, `uvicorn`.
- **APIs Externas:** Amazon Creators API (LWA), OpenAI API (GPT-4/GPT-3.5), Telegram Bot API.
- **Despliegue:** Docker, Docker Compose, PyInstaller (para el .exe).

## 🚀 Comandos Clave

### Desarrollo y Ejecución
- **Lanzar Interfaz Gráfica:**
  ```bash
  python run_gui.py
  ```
- **Lanzar Servidor Local (FastAPI):**
  ```bash
  uvicorn src.server.nas_api:app --reload --port 8000
  ```

### Construcción y Despliegue
- **Generar Ejecutable para Windows:**
  ```bash
  pyinstaller PublicadorBuenChollo.spec --noconfirm
  ```
- **Despliegue en Docker (NAS):**
  ```bash
  docker-compose up -d --build
  ```

## ⚙️ Configuración (.env)

El archivo `.env` es crítico y debe contener:
- `AMAZON_CLIENT_ID` / `AMAZON_CLIENT_SECRET`: Credenciales de Amazon.
- `AMAZON_AFFILIATE_TAG`: Tu ID de afiliado.
- `OPENAI_API_KEY`: Para la generación de textos.
- `TELEGRAM_BOT_TOKEN`: Token de @BotFather.
- `TELEGRAM_CHANNEL_ID`: ID del canal principal.
- `NAS_SERVER_URL`: URL del servidor FastAPI (ej. `http://192.168.1.50:8000`).

## 📂 Convenciones del Proyecto

- **Estructura de Carpetas:**
    - `src/cli/`: Scripts de utilidad y migración.
    - `src/integrations/`: Todo el código de comunicación con servicios externos.
    - `data/`: Almacenamiento persistente local (catálogos JSON).
    - `runtime/`: Archivos temporales y de sesión de Telegram.
- **Formateo de Mensajes:** Se utiliza un sistema de mapeo de emojis a `custom_emoji_id` para aprovechar los iconos premium de Telegram.
- **Imágenes:** Soporta carrusel de hasta 7 variantes de Amazon o subida de fotos locales personalizadas.
