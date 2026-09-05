# Funcionalidad

Documentación funcional detallada de las aplicaciones de **Amazon-Api-Apps**.

---

## 1. Buscador de Chollos — `run_deals_gui.py`

Ventana de **solo consulta**: explora ofertas de Amazon antes de decidir cuáles publicar. No publica nada.

### 1.1 Búsqueda por categoría

- **24 categorías tech** definidas en `src/domain/categories_search_index.py` (mapa `CATEGORY_SEARCH_MAP`):

  - Informática y software · Videojuegos · Electrónica
  - TV, home cinema y películas · Móviles y accesorios
  - Auriculares, altavoces y música · Tabletas · Informática
  - Tecnología para vestir · Equipos de audio y Hi-Fi · Audio y vídeo portátil
  - Auriculares · Fotografía y videocámaras · GPS y accesorios
  - Accesorios de alimentación · Pilas y cargadores
  - Lectores de eBooks y accesorios · Radiocomunicación
  - Telefonía fija y accesorios
  - **Software y suscripciones · Smart home y domótica · Impresoras y consumibles · Almacenamiento y discos · Redes y WiFi** *(añadidas el 2026-08-29)*

- Cada categoría usa un `search_index`, un `browse_node_id`, **o** palabras `keywords` (o combinación), según lo que devuelva mejores chollos.
- Filtros: **descuento mínimo/máximo (%)** y **número de resultados** ("Max" = sin límite).
- Valores por defecto: descuento **15%–50%**, cantidad Max.

### 1.2 Estrategia de búsqueda — `FindDealsUseCase`

Para maximizar la cobertura de chollos, el caso de uso ejecuta un **doble barrido** por categoría:

1. **Rotación de `SortBy`** (5 estrategias: Destacados, Precio ↑/↓, Novedades, Valoración). Cada criterio devuelve un ranking parcialmente distinto; se deduplica por ASIN.
2. **Barrido por marcas de calidad**: usa las marcas curadas del mapa marcas→categorías (`MARCAS_POR_CATEGORIA`) más las marcas de calidad que aparezcan en los **refinements** de la categoría. Se ignoran las marcas genéricas chinas (p.ej. BROTECT, MOKO) que antes dominaban el barrido.

Detalles clave de la API:

- Se pide a la API el **descuento real** (`min_saving_percent`): por defecto el mismo `min_descuento` configurado (configurable con `min_saving_percent_api`). El filtro local sigue como red de seguridad.
- La API **CAPA** `itemCount` a 10 y `itemPage` a 10 (techo ~100 por query).
- La paginación solo se corta al llegar a una **página vacía** (nunca por página corta).
- `total_result_count` es **global/capeado**: no sirve para decidir cuándo cortar.
- ~1 petición/segundo para no ser rechazado por Amazon.

**Orden "calidad primero"**: `priorizar_marcas=True` (por defecto) ordena las marcas de calidad antes que el resto (a igual señal, mayor descuento). Con `False`, vuelve al orden por descuento.

### 1.3 Tabla de resultados

| Columna | Significado |
|---|---|
| **Dto.** | % de descuento (ej. `-30%`). |
| **Marca** | Nombre; las marcas de calidad se marcan con **★ y en verde**. |
| **Producto** | Título. |
| **Precio** | Precio actual con moneda. |

### 1.4 Detalle y gráfica Keepa

Al seleccionar un producto:

- Muestra el **título**, **precio** (y anterior con %), **fecha de caducidad** de la oferta (si existe) y la **URL**.
- Carga la **gráfica de precio histórico de Keepa** (`graph.keepa.com/pricehistory.png`) y la imagen principal, cada una en su propio hilo.
- Botón para **abrir en Amazon**.

### 1.5 Ordenación por fecha de caducidad

Botón **"📅 Caducidad"**: cicla entre sin orden → ascendente (más pronto) → descendente (más tarde). Los chollos **sin fecha van siempre al final**.

### 1.6 Barrido completo

Botón **"⚡ Buscar TODOS los chollos"**: recorre las 24 categorías con el doble barrido, guarda automáticamente `data/max_ofertas_<fecha>.json` y muestra todos los resultados.

### 1.7 Cargar resultados previos

Botón **"📂 Cargar resultados"**: abre un JSON del barrido (`data/max_ofertas_*.json`) y lo muestra en la tabla con su detalle/Keepa, sin volver a golpear la API de Amazon.

### 1.8 Filtro de calidad (marcas)

Panel **"⭐ Filtro de calidad"**: descarta marcas no fiables según `MARCAS_CALIDAD` (`src/domain/marcas_calidad.py`). Incluye la normalización de sufijos ("Sony Inc." → sony) y el match por primera palabra ("Soundcore by Anker" → soundcore).

> ⚠️ La Amazon Creators API **no** devuelve `customerReviews` (verificado en vivo 2026-08-01) → no hay dato fiable de valoración/estrellas para filtrar; el criterio de valoración se descartó.

### 1.9 Filtrado por Keepa (opcional, de pago)

Panel **"🎯 Filtrado por Keepa"**: aplica `FilterDealsKeepaUseCase`, que consulta el histórico de precios de Keepa (serie NEW→AMAZON, dominio ES, últimos N días) y detecta **descuento real vs señuelo**:

- Pasa si el precio está en el mínimo del período, cae desde un precio estable, o hay tendencia descendente.
- Descarta "sondas" (oscilación constante) y bajadas desde precio inflado.

⚠️ **Requiere `KEEPA_API_KEY`** (API de pago ~60 €/mes). Sin clave, devuelve la lista sin filtrar. Métricas configurables: ahorro vs media %, margen sobre mínimo histórico %, días de historia mínimos.

---

## 2. Generador / Publicador de Ofertas — `run_gui.py`

Ventana principal para **crear y publicar** un post de oferta en Telegram.

### 2.1 Extracción de datos de Amazon

- Pega un enlace (largo, corto `amzn.to`) o un **ASIN** directo.
- Detecta automáticamente el ASIN.
- Obtiene: título, precio actual, **precio anterior**, cálculo automático de **ahorro (€ y %)**.
- **Ofertas Flash**: detecta la fecha de expiración y añade aviso dinámico (ej. "⏳ Finaliza el 12 de agosto").

### 2.2 Escritura con IA (OpenAI)

- `GPTService` toma las características técnicas y genera un **texto de venta** cercano, atractivo y sintetizado.
- Limpieza automática de espacios/tabuladores: el post queda impecable.

### 2.3 Sistema de imágenes

- **Carrusel de fotos**: al pegar el enlace se navegan las imágenes del producto (hasta 7) para elegir la mejor.
- **Subida de capturas**: botón "Subir propia foto" para usar una imagen propia del chollo.

### 2.4 Categorías y hashtags

- Gestión de categorías del post.
- Catálogo de categorías mantenido en `data/` (`json_category_repository.py`).
- Hashtags generados y normalizados (`hashtag_rules.py`).

### 2.5 Publicación en Telegram

- Formatea el mensaje con `telegram_formatter.py` (negritas, precios, **emojis premium `<tg-emoji>`**).
- Publica **imagen + texto** directamente en el canal/grupo configurado vía `publisher_service.py`.
- Envía el post al canal si la fecha de expiración existe (aviso de oferta flash).

---

## 3. API NAS — `src/server/nas_api.py`

"Cerebro" desplegado en Synology (Docker). Recibe publicaciones programadas desde Windows, las guarda en SQLite local y un **guardián (daemon)** las publica en Telegram cuando llega la hora.

| Endpoint | Método | Función |
|---|---|---|
| `/api/schedule` | POST | Agenda una publicación (guarda en SQLite). |
| `/api/status` | GET | Devuelve el estado del servidor/cola. |

---

## 4. Scripts y CLI

| Script | Función |
|---|---|
| `scripts/test_busqueda_max_ofertas.py` | Barrido máximo de ofertas (sin GUI) → `data/max_ofertas_<fecha>.json`. Flags: `--min`, `--max`, `--api-min`, `--sin-priorizar-marcas`, `--sin-marcas`, `--max-marcas`, `--paginas-marca`, `--marcas-calidad`. |
| `scripts/explore_search_nodes.py` | Sondeo de `search_index` / `browse_node_id` / `keywords` en vivo (verificado contra la API). |
| `scripts/explore_deals_depth.py` | Explora la profundidad de resultados de una categoría. |
| `scripts/extract_channel_data.py` | Extrae datos del canal (para el catálogo). |
| `scripts/process_catalog.py` | Procesa el catálogo de categorías. |
| `scripts/refine_catalog.py` | Refina/limpia el catálogo. |
| `src/cli/sync_categories.py` | Sincroniza categorías desde el canal. |
| `src/cli/migrate_categories.py` | Migra el esquema de categorías. |