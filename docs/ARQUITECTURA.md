# Arquitectura

Documentación de arquitectura de **Amazon-Api-Apps**: capas, módulos, responsabilidades y reglas de diseño.

---

## 1. Visión general

El proyecto sigue **Clean Architecture estricta**. Las dependencias apuntan siempre hacia el centro (el dominio), nunca al revés:

```
┌────────────────────────────────────────────────────────────────┐
│                        UI (Tkinter)                           │
│              src/ui/deals_gui.py · main_gui.py                │
├────────────────────────────────────────────────────────────────┤
│                     Use Cases (orquesta)                      │
│                    src/use_cases/* + ports/                   │
├────────────────────────────────────────────────────────────────┤
│              Domain (lógica pura, sin I/O)                    │
│     entities · categories · marcas_calidad · keepa_metrics    │
├────────────────────────────────────────────────────────────────┤
│      Services (fachadas)   ·   Formatters (formato puro)      │
├────────────────────────────────────────────────────────────────┤
│      Integrations (APIs externas: Amazon, OpenAI, Keepa,      │
│           Telegram, Storage) + Config + Server                │
└────────────────────────────────────────────────────────────────┘
```

**Principio rector**: la lógica de negocio vive en `domain/` (pura) y la orquestación en `use_cases/`. La UI no contiene lógica de negocio; solo llama a casos de uso y muestra resultados.

---

## 2. Capas y responsabilidades

### 2.1 `src/domain/` — Reglas de negocio puras

Sin IO, sin dependencias externas, sin imports de otras capas.

| Módulo | Contenido |
|---|---|
| `entities.py` | `ProductInfo` (ASIN, título, marca, precios, descuento, valoración, URL, imagen, fin de oferta) y otras entidades. |
| `categories_search_index.py` | `CATEGORY_SEARCH_MAP`: mapa de **24 categorías tech** → `search_index` / `browse_node_id` / `keywords` + auxiliares `resolve_category`, `canonical_name`. |
| `marcas_calidad.py` | `MARCAS_CALIDAD`: lista de marcas fiables; `MARCAS_POR_CATEGORIA` (marcas→categorías); normalización de nombres (sufijos legales, primera palabra). |
| `keepa_metrics.py` | Métricas puras de validación Keepa (ahorro vs media, margen sobre mínimo, detección de señuelo). |
| `hashtag_rules.py` | Normalización de hashtags para los posts. |
| `category.py` | Entidad de categoría del catálogo. |

### 2.2 `src/use_cases/` — Orquestación (DI)

Reciben servicios por **constructor** (inyección de dependencias); no instancian integraciones directamente (salvo los valores por defecto de conveniencia). Los `ports/` definen interfaces de repositorio para inyectar en las integraciones.

| Caso de uso | Responsabilidad |
|---|---|
| `find_deals.py` | Buscar chollos por categoría (rotación de SortBy + barrido por marcas de calidad + filtros locales). |
| `generate_post.py` | Crear el post: datos de Amazon + resumen de IA (OpenAI) + formateador Telegram. |
| `filter_deals_keepa.py` | Valorar con Keepa si el descuento es real o un señuelo. |
| `filter_chollos_calidad.py` | Descartar marcas no fiables según `MARCAS_CALIDAD`. |
| `build_category_catalog_from_channel.py` | Construir el catálogo de categorías desde el historial del canal de Telegram. |
| `get_categories_for_ui.py` | Devolver categorías para la UI. |
| `upsert_categories_from_post.py` | Insertar/actualizar categorías nuevas detectadas en posts. |

#### Puertos (ports)

- `category_repository.py` → interfaces CRUD de categorías.
- `channel_history_reader.py` → interfaz para leer historial de canales.
- `keepa_repository.py` → interfaz para consultar histórico de precios Keepa.

### 2.3 `src/services/` — Fachadas internas

| Módulo | Responsabilidad |
|---|---|
| `amazon_service.py` | Fachada sobre la API de Amazon (búsqueda, refinements de marcas, datos de producto). Aísla la lógica de negocio de los detalles técnicos. |
| `publisher_service.py` | Fachada de publicación a Telegram (mensaje + foto). |

### 2.4 `src/formatters/` — Formato puro

| Módulo | Responsabilidad |
|---|---|
| `telegram_formatter.py` | Áplica el formato final del post: negritas, precios, emojis premium `<tg-emoji>`. |

### 2.5 `src/integrations/` — APIs externas

Tocan APIs externas; capturan errores de red/API y los traducen o devuelven `None` + `logging` (nunca propagan excepciones crudas hacia la UI).

| Integración | Módulo | Detalles |
|---|---|---|
| Amazon | `amazon/amazon_api.py` | Amazon Creators API v3.2 (PA-API): `search_products`, `get_product_data`, `get_brand_refinements`. |
| Amazon auth | `amazon/lwa_auth.py` | OAuth LWA (nuevo flujo 2026). |
| OpenAI | `openai/gpt_service.py` | Redacción del texto de venta con ChatGPT. |
| Keepa | `keepa/keepa_client.py` | Histórico de precios Keepa (API de pago). |
| Telegram (bot) | `telegram/telegram_api.py` | Publicación de mensajes/fotos vía bot (peticiones web directas, sin librería pesada). |
| Telegram (historial) | `telegram/telegram_history_reader.py` | Lee mensajes antiguos con Telethon (sesión de usuario). |
| Telegram (emojis) | `telegram/emoji_mapper.py` | Mapeo de emojis premium. |
| Storage | `storage/json_category_repository.py` | Persistencia del catálogo en JSON (`data/`). |
| Storage | `storage/deals_json.py` | Serialización de ofertas: `guardar_ofertas_json` / `productos_desde_json` (formato compartido GUI↔script). |

### 2.6 `src/config/` — Configuración

`settings.py` carga `.env` al importarse (python-dotenv). **Acceso siempre vía `Config`; nunca hardcodear credenciales.**

### 2.7 `src/server/` — API REST (NAS)

`nas_api.py` es un **FastAPI** desplegado en Synology (Docker). Actúa como "cerebro":
- `POST /api/schedule` → agenda una publicación (guarda en SQLite local).
- `GET /api/status` → estado.
- Un **daemon** las publica en Telegram cuando llega la hora.

### 2.8 `src/ui/` — Interfaces de escritorio

- `deals_gui.py` → buscador de chollos (solo consulta).
- `main_gui.py` → generador/publicador de posts.

Ambas envuelven llamadas a casos de uso en `try/except` con `messagebox` para que la app no se cierre ante errores.

### 2.9 `src/cli/` — Utilidades de consola

`sync_categories.py`, `migrate_categories.py`, `find_deals.py`, `main.py` → mantenimiento de catálogo y búsquedas por consola.

---

## 3. Reglas críticas de capas

1. **No cruzar capas**: `domain/` no importa integraciones; la UI no hace lógica de negocio.
2. **DI en use cases**: reciben repositorios/servicios por constructor.
3. **Errores en integraciones**: capturar y traducir/`None` + log, nunca lanzar hacia la UI.
4. **Formato puro**: `formatters/` no hace IO.
5. **Config centralizada**: credenciales siempre vía `Config`, nunca hardcoded.

---

## 4. Flujo de datos (buscador de chollos)

```
UI (deals_gui)  →  FindDealsUseCase.execute()/execute_todas()
                 →  AmazonService.search_deals() / get_brand_refinements()
                 →  AmazonAPI.search_products()  (PA-API + LWA)
                 →  ProductInfo[]
                 →  filtros locales (descuento, calidad, orden)
                 →  Treeview (GUI)  o  JSON (storage/deals_json)
```

## 5. Flujo de datos (generador de posts)

```
UI (main_gui)  →  GeneratePostUseCase.execute(url)
               →  AmazonService (datos del producto)
               →  GPTService (resumen de venta)
               →  TelegramFormatter (mensaje formateado)
               →  PublisherService (publica en Telegram)
```

---

## 6. Dependencias externas

Ver `requirements.txt`:

- `requests` · `Pillow` · `ttkbootstrap` — UI y descargas.
- `fastapi` · `uvicorn` — API NAS.
- `telethon` — lectura de historial de canales (sesión de usuario).
- `python-dotenv` — configuración `.env`.
- `amazon-creatorsapi-python-sdk` — SDK oficial de la Creators API v3.2.
- `keepa` — cliente de la API Keepa.
- `pytest` — testing.