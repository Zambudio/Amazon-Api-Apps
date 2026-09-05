# Arquitectura y Flujo Técnico

Este documento detalla cómo interactúan los componentes del sistema y el flujo de procesamiento de un "chollo".

## 1. Visión de capas (Clean Architecture)

```
┌─────────────────────────────────────────────────────────┐
│  UI (Tkinter): src/ui/deals_gui.py · main_gui.py        │
├─────────────────────────────────────────────────────────┤
│  Use Cases (orquesta, DI): src/use_cases/* + ports/*    │
├─────────────────────────────────────────────────────────┤
│  Domain (pura, sin I/O): src/domain/*                   │
├─────────────────────────────────────────────────────────┤
│  Services + Formatters                                  │
├─────────────────────────────────────────────────────────┤
│  Integrations + Config + Server                         │
└─────────────────────────────────────────────────────────┘
```

**Regla crítica:** las dependencias apuntan al centro. `domain/` no hace IO; `ui/` no contiene lógica de negocio; `use_cases/` recibe servicios por constructor.

## 2. Flujo de generación de un post (Publicador)

1. **Entrada:** URL de Amazon o ASIN.
2. **Extracción (`AmazonService` → `amazon_api`):** título, precios (actual + anterior), descuento, descripción larga, imágenes y oferta flash (fecha de expiración).
3. **Enriquecimiento (`GPTService`):** envía la descripción técnica a ChatGPT para generar el "copy" atractivo y corto; se pasan las categorías existentes para que elija las más adecuadas.
4. **Formateo (`TelegramFormatter`):** construye el string final aplicando negritas, estructura de precios, cálculo de % y **emojis premium** (`<tg-emoji>`).
5. **Publicación (`PublisherService` → `TelegramBotAPI`):** envía la imagen + texto al canal/grupo de Telegram (Bot API).

## 3. Flujo de búsqueda de chollos (Buscador)

1. **Entrada:** categoría + rango de descuento + cantidad.
2. **Barrido (`FindDealsUseCase` → `AmazonService`):**
   - Rotación de `SortBy` (5 estrategias) con deduplicación por ASIN.
   - Barrido por **marcas de calidad** (mapa `MARCAS_POR_CATEGORIA` + refinements), ignorando genéricas.
   - Se pide a la API el descuento real (`min_saving_percent`); el filtro local es red de seguridad.
3. **Filtros locales:** descuento fuera de rango, calidad de marca, orden "calidad primero".
4. **Salida:** tabla en `deals_gui` o JSON en `data/` (`deals_json.py`).

## 4. Flujo de valoración con Keepa

1. `FilterDealsKeepaUseCase` consulta `KeepaClient` (serie NEW→AMAZON, dominio ES, N días).
2. Reglas puras en `src/domain/keepa_metrics.py`: descuento real vs señuelo (pasa si está en mínimo del período, cae desde precio estable o hay tendencia descendente; descarta sondas e infladas).
3. **Desactivado por coste**: requiere `KEEPA_API_KEY`; sin clave devuelve la lista sin filtrar.

## 5. Catálogo de categorías

- `src/domain/categories_search_index.py`: mapa de **24 categorías tech** → `search_index` / `browse_node_id` / `keywords`.
- `json_category_repository.py`: persistencia del catálogo en `data/`.
- `build_category_catalog_from_channel.py`: construye/actualiza el catálogo leyendo el historial del canal (Telethon).

## 6. Estructura detallada

- `src/`: núcleo de la aplicación (domain, use_cases, services, integrations, ui, cli, server, config, formatters).
- `scripts/`: barridos de ofertas y sondeos de nodos en vivo.
- `docs/`: manuales y guías (ARQUITECTURA, FUNCIONALIDAD, DESARROLLO, buscador_chollos, KeepaImplementacion).
- `assets/`: logos y recursos estáticos.
- `deploy/`: todo lo necesario para el despliegue en Docker/NAS (Dockerfile.nas, docker-compose, GUIA_SYNOLOGY).
- `data/`: JSON de catálogo y de ofertas (`max_ofertas_*.json`, `explore_nodes_*.json`).
- `tests/`: suite de pruebas (unit + integration).

## 7. Sistema de emojis premium

- Archivo clave: `src/integrations/telegram/emoji_mapper.py`.
- Reemplaza emojis estándar por tags `<tg-emoji id="...">`, que solo muestran el emoji premium (canales con boost o cuentas premium), dando un aspecto visual superior.

## 8. Despliegue y construcción

- **Windows:** PyInstaller con `PublicadorBuenChollo.spec` (publicador) y `BuscarChollos.spec` (buscador); incluyen icono y bundle de dependencias. Python 3.14 en `%LOCALAPPDATA%\Programs\Python\Python314`.
- **Servidor:** Dockerizado con `deploy/Dockerfile.nas` y `docker-compose.yml`, optimizado para Synology. Expone `:8000` (FastAPI: `POST /api/schedule`, `GET /api/status`).

Documentación completa y actualizada: `docs/ARQUITECTURA.md`, `docs/FUNCIONALIDAD.md`, `docs/DESARROLLO.md`.