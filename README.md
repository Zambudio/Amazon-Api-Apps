# Amazon-Api-Apps

Suite de herramientas para encontrar y publicar chollos de Amazon en Telegram, con ayuda de IA (OpenAI) y datos de precios de Keepa.

El proyecto tiene dos aplicaciones de escritorio (GUI en Tkinter/ttkbootstrap) independientes, más una capa de dominio/casos de uso compartida siguiendo Clean Architecture.

## Qué hace cada GUI

### 🛒 `run_deals_gui.py` — Buscador de Chollos
Ventana de **solo consulta**, no publica nada. Sirve para explorar ofertas antes de decidir cuáles publicar.

- Busca productos en oferta de Amazon por **categoría**, con filtro de **descuento mínimo/máximo (%)** y **número de resultados**.
- Muestra los resultados en una tabla (descuento, título, precio).
- Al seleccionar un producto, carga su **gráfica de precio histórico de Keepa** y un botón para abrirlo directamente en Amazon.

Lógica principal: [`src/ui/deals_gui.py`](src/ui/deals_gui.py) → [`src/use_cases/find_deals.py`](src/use_cases/find_deals.py) → [`src/services/amazon_service.py`](src/services/amazon_service.py) → [`src/integrations/amazon/amazon_api.py`](src/integrations/amazon/amazon_api.py).

### 📢 `run_gui.py` — Generador de Ofertas para Telegram
Ventana principal para **crear y publicar** un post de oferta.

- Pega un enlace (o ASIN) de Amazon y extrae automáticamente título, precio, descuento, ofertas flash con fecha de expiración, etc.
- Usa **ChatGPT (OpenAI)** para redactar el texto de venta a partir de las características del producto.
- Carrusel de imágenes del producto (hasta 7) o subida de una captura propia.
- Gestión de categorías y hashtags del post.
- Publica la imagen + texto directamente en el **canal/grupo de Telegram** configurado (bot de Telegram + sesión de usuario Telethon para leer canales).

Lógica principal: [`src/ui/main_gui.py`](src/ui/main_gui.py) → [`src/use_cases/generate_post.py`](src/use_cases/generate_post.py) y [`src/services/publisher_service.py`](src/services/publisher_service.py).

Documentación adicional de esta GUI (funcionalidades detalladas, capturas conceptuales): [`docs/README.md`](docs/README.md).

## Estructura del proyecto

```
src/
  domain/         Entidades y reglas de negocio puras (ProductInfo, categorías, hashtags...)
  use_cases/       Orquestación: buscar chollos, generar post, gestionar categorías
  services/         Fachadas de negocio sobre las integraciones externas
  integrations/     Clientes de APIs externas (Amazon PA-API, OpenAI, Telegram, almacenamiento)
  ui/               Las dos GUIs (Tkinter + ttkbootstrap)
  cli/              Variantes de línea de comandos de algunos casos de uso
  config/           Carga de configuración (.env) y rutas de la app
  server/           API auxiliar (FastAPI) para despliegue en NAS
data/               Catálogo de categorías y datos auxiliares
deploy/             Dockerfile y docker-compose para desplegar en Synology NAS
tests/              Tests unitarios e de integración (pytest)
run_deals_gui.py    Lanzador del Buscador de Chollos
run_gui.py          Lanzador del Generador de Ofertas para Telegram
```

## Configuración

El proyecto se configura mediante variables de entorno en un archivo **`.env`** en la raíz (ya incluido en este repositorio privado). Las variables usadas son:

| Variable | Para qué sirve |
|---|---|
| `AMAZON_CLIENT_ID` / `AMAZON_CLIENT_SECRET` | Credenciales de la API de Amazon (Product Advertising API / Creators API) |
| `AMAZON_AFFILIATE_TAG` | Tu ID de afiliado de Amazon |
| `AMAZON_API_VERSION` / `AMAZON_AUTH_ENDPOINT` / `AMAZON_OAUTH_SCOPE` | Parámetros técnicos de conexión a la API de Amazon |
| `OPENAI_API_KEY` | Clave de OpenAI para generar los textos de venta |
| `TELEGRAM_BOT_TOKEN` | Token del bot (creado con @BotFather) que publica los posts |
| `TELEGRAM_ADMIN_CHANNEL_ID` | Canal/grupo donde se revisan los posts antes de publicar |
| `TELEGRAM_MAIN_CHANNEL_ID` | Canal principal donde se publican las ofertas |
| `TELEGRAM_USER_API_ID` / `TELEGRAM_USER_API_HASH` | Credenciales de una app de Telegram (para leer canales con Telethon) |
| `TELEGRAM_USER_SESSION` | Ruta al archivo de sesión de Telethon (`runtime/telegram_user.session`) |

> ⚠️ El `.env` y el archivo de sesión de Telegram contienen credenciales reales. Este repositorio es **privado**; no lo hagas público ni compartas su contenido.

## Cómo ejecutarlo

1. Crea y activa un entorno virtual, e instala las dependencias:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate      # Windows
   pip install -r requirements.txt
   ```
2. Asegúrate de que el archivo `.env` de la raíz tiene las claves correctas (ver tabla anterior).
3. Ejecuta la GUI que necesites:
   ```bash
   python run_deals_gui.py   # Buscador de Chollos (solo consulta)
   python run_gui.py         # Generador y publicador de ofertas en Telegram
   ```

También existe un ejecutable ya compilado del publicador en `dist/PublicadorBuenChollo/PublicadorBuenChollo.exe` (generado con PyInstaller, ver `PublicadorBuenChollo.spec`), pensado para usarse sin abrir el código.

## Tests

```bash
pytest
```

- `tests/unit`: lógica pura (formateadores, normalización, filtros de búsqueda).
- `tests/integration`: flujo completo de casos de uso.
