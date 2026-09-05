# 📋 Info_Proyecto_Python.md - Contexto Completo del Proyecto Publicador BuenChollo

Este documento proporciona un contexto completo del proyecto **Publicador BuenChollo**, un sistema para automatizar la publicación de ofertas de Amazon en canales de Telegram. Está diseñado para ser utilizado por herramientas como Cloud Code o agentes de IA para entender la arquitectura, funcionalidades y estructura del código.

## 🚀 Resumen del Proyecto

**Publicador BuenChollo** es una aplicación Python que transforma enlaces de productos de Amazon en posts atractivos para Telegram, utilizando IA (GPT) para enriquecer el contenido y un formato visual premium con emojis animados. Soporta dos modos de operación:

1. **GUI (Desktop):** Interfaz gráfica para gestión manual en Windows.
2. **Server (NAS/Synology):** API FastAPI para ejecución autónoma y programada.

### Tecnologías Clave
- **Lenguaje:** Python 3.11+
- **Arquitectura:** Clean Architecture (separación de capas: domain, use_cases, services, integrations, ui)
- **Interfaz:** ttkbootstrap (Tkinter moderno) para GUI, FastAPI para servidor
- **APIs Externas:**
  - Amazon Creators API v3.2 (LWA) para extracción de datos de productos
  - OpenAI API (GPT-4o/GPT-3.5-turbo) para síntesis de textos y categorización
  - Telegram Bot API & Telethon para publicación y lectura de histórico
- **Persistencia:** JSON para categorías, reglas de hashtags y datos temporales
- **Despliegue:** PyInstaller para EXE, Docker para contenedores

## 📂 Estructura del Proyecto

El proyecto sigue una arquitectura limpia con separación estricta de responsabilidades. A continuación, la estructura detallada:

### Raíz del Proyecto
- `AGENTS.md`: Directrices operativas para agentes de IA (mandatos prioritarios, comandos de desarrollo, estructura del proyecto)
- `PublicadorBuenChollo.spec`: Configuración para PyInstaller (construcción del EXE)
- `run_gui.py`: Script de lanzamiento de la interfaz gráfica
- `requirements.txt` (implícito en deploy/): Dependencias Python

### Carpetas Principales

#### `src/` - Código Fuente (Núcleo de la Aplicación)
- **`domain/`**: Lógica pura y reglas de negocio
  - `category.py`: Entidades y reglas para categorías de productos
  - `entities.py`: Definiciones de entidades principales (Producto, Post, etc.)
  - `hashtag_rules.py`: Reglas para generación automática de hashtags
- **`use_cases/`**: Orquestación de servicios e integraciones
  - `build_category_catalog_from_channel.py`: Construye catálogo de categorías desde canal de Telegram
  - `generate_post.py`: Caso de uso principal para generar un post completo
  - `get_categories_for_ui.py`: Obtiene categorías para la interfaz
  - `upsert_categories_from_post.py`: Actualiza categorías desde posts
  - `ports/`: Interfaces abstractas (category_repository.py, channel_history_reader.py)
- **`services/`**: Fachadas de servicios
  - `amazon_service.py`: Servicio para integración con Amazon API
  - `publisher_service.py`: Servicio para publicación en Telegram
- **`integrations/`**: Adaptadores para APIs externas
  - `amazon/`: Integración con Amazon
    - `amazon_api.py`: Cliente para Amazon Creators API
    - `lwa_auth.py`: Gestor de token LWA (Login With Amazon), inyectado en el cliente de la SDK
  - `openai/`: Integración con OpenAI
    - `gpt_service.py`: Servicio para llamadas a GPT
  - `storage/`: Persistencia
    - `json_category_repository.py`: Repositorio JSON para categorías
  - `telegram/`: Integración con Telegram
    - `emoji_mapper.py`: Mapeo de emojis estándar a custom emojis premium
    - `telegram_api.py`: Cliente para Telegram Bot API
    - `telegram_history_reader.py`: Lectura de histórico de canales
- **`ui/`**: Interfaz gráfica
  - `main_gui.py`: Interfaz principal con ttkbootstrap
- **`server/`**: API para servidor NAS
  - `nas_api.py`: API FastAPI para ejecución autónoma
- **`config/`**: Configuraciones
  - `settings.py`: Gestión de configuración y variables de entorno (.env)
- **`cli/`**: Scripts de línea de comandos
  - `main.py`: Punto de entrada CLI
  - `migrate_categories.py`: Migración de categorías
  - `sync_categories.py`: Sincronización de categorías

#### `docs/` - Documentación
- `README.md`: Guía de uso general
- `GEMINI.md`: Documentación específica para integración con Gemini (posiblemente IA)

#### `context/` - Documentación para IA
- `arquitectura.md`: Detalles técnicos de arquitectura y flujo
- `contextoIA.md`: Contexto principal para agentes de IA
- `instrucciones_ia.md`: Guía de desarrollo e instrucciones para IAs

#### `assets/` - Recursos Estáticos
- Logos, iconos y recursos visuales

#### `build/` - Archivos de Construcción
- `PublicadorBuenChollo/`: Salida de PyInstaller (EXE y dependencias empaquetadas)

#### `data/` - Datos y Catálogos
- `categories.json`: Categorías de productos
- `raw_amazon.json`: Datos crudos de Amazon
- `todos_los_productos.json`: Catálogo completo de productos

#### `deploy/` - Despliegue
- `docker-compose.yml`: Configuración Docker
- `Dockerfile.nas`: Dockerfile para NAS/Synology
- `GUIA_SYNOLOGY.md`: Guía de despliegue en Synology
- `requirements_server.txt`: Dependencias para servidor

#### `runtime/` - Archivos en Tiempo de Ejecución
- `telegram_user.session`: Sesión de Telethon
- `temp_deal_details.txt`: Archivos temporales

#### `scripts/` - Utilidades
- `convert_logo.py`: Conversión de logos
- `extract_channel_data.py`: Extracción de datos de canales
- `process_catalog.py`: Procesamiento de catálogos
- `refine_catalog.py`: Refinamiento de catálogos

#### `tests/` - Pruebas
- `integration/`: Pruebas de integración
  - `test_build_catalog.py`
  - `test_generate_post.py`
- `unit/`: Pruebas unitarias
  - `test_amazon_api.py`
  - `test_domain.py`
  - `test_formatters.py`

## 🔄 Flujo de Funcionamiento

### Flujo Principal de Generación de Post
1. **Entrada:** URL de Amazon o ASIN
2. **Extracción (AmazonService):** Consulta API de Amazon para obtener título, precios, descripción, imágenes
3. **Enriquecimiento (GPTService):** Envía descripción a GPT para generar copy atractivo y seleccionar categorías
4. **Formateo (TelegramFormatter):** Construye string final con negritas, emojis premium, cálculos de descuento
5. **Publicación (PublisherService):** Envía imagen y texto a Telegram vía Bot API

### Sistema de Emojis Premium
- Utiliza custom emojis de Telegram para apariencia superior
- Mapeo en `emoji_mapper.py`: Convierte emojis estándar a `<tg-emoji id="...">`

### Persistencia y Categorización
- Categorías almacenadas en JSON
- Reglas de hashtags automáticas
- Sincronización desde canales de Telegram

## 🛠️ Comandos de Desarrollo

- **Lanzar GUI:** `python run_gui.py`
- **Lanzar Servidor (NAS):** `uvicorn src.server.nas_api:app --host 0.0.0.0 --port 8000`
- **Pruebas:** `pytest`
- **Construcción EXE:** `pyinstaller PublicadorBuenChollo.spec --noconfirm`
- **Docker:** `docker-compose -f deploy/docker-compose.yml up --build`

## ⚙️ Configuración

- Archivo `.env` para credenciales (Amazon, OpenAI, Telegram)
- No commitear `.env`
- Configuración centralizada en `src/config/settings.py`

## 🧪 Testing y Validación

- Tests obligatorios para nueva funcionalidad
- Cobertura en `tests/` (unitarios e integración)
- Validación pre-commit: Funcionalidad terminada y tests pasan

## 🚀 Gestión de Git y Documentación

- **Commits Manuales:** Requiere confirmación explícita del usuario
- **Regla Triple:** Actualizar `AGENTS.md`, `docs/`, `context/` por cada cambio funcional
- **Sugerencia Pre-Commit:** Antes de commit, sugerir actualización de `context/`

## 📝 Notas para IA/Cloud Code

- **Arquitectura Limpia:** Respeta separación de capas estrictamente
- **Código Limpio:** Legibilidad, nombres descriptivos, Type Hints
- **Documentación Junior-Friendly:** Encabezados en archivos `.py` explicando función
- **PEP 8:** Seguir estándares Python
- **Logging:** Usar `logging`, no `print()`
- **Seguridad:** Nunca incluir `.env` en commits
- **Testing:** Toda nueva funcionalidad requiere tests

Este documento debe mantenerse actualizado junto con el código. Para cambios, actualizar también `context/` y `docs/`.