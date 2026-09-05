# AGENTS.md — Guía Operativa (Alta Señal)

Solo incluye lo que un agente podría hacer mal sin contexto del repo.

## Reglas críticas
- Mantener **Clean Architecture** estricta (no cruzar capas):
  - `src/domain/`: lógica pura, sin IO ni dependencias externas
  - `src/use_cases/`: orquesta; recibe servicios por constructor (DI)
  - `src/formatters/`: formato puro (texto Telegram, emojis, %)
  - `src/services/`: fachadas internas sobre integraciones
  - `src/integrations/`: toca APIs externas; captura errores de red/API y los traduce o devuelve `None` + log
- Toda funcionalidad nueva o modificada => **tests en `tests/` obligatorios**
- Cada `.py` empieza con **docstring de cabecera** (qué hace y contexto)
- Regla triple de doc: cada cambio funcional => `AGENTS.md` + `docs/` + `context/`
- No usar `print()`: usar `logging`

## Comandos (no asumir defaults)
- GUIs desde la raíz (así funcionan los imports `src.*`):
  - Buscador de chollos: `python run_deals_gui.py`
  - Generador/publicador de ofertas: `python run_gui.py`
- API NAS (FastAPI): `uvicorn src.server.nas_api:app --host 0.0.0.0 --port 8000`
- Tests: `pytest` · foco: `pytest tests/unit -q` · `pytest tests/integration -q`
- Build EXE: `pyinstaller PublicadorBuenChollo.spec --noconfirm`
  - El spec asume Python 3.14 con site-packages en `%LOCALAPPDATA%\Programs\Python\Python314`
  - Buscador de chollos: `pyinstaller BuscarChollos.spec --noconfirm` → `dist/BuscarChollos/BuscarChollos.exe` (GUI de `run_deals_gui.py`, icono `assets/logo.ico`); también hay un script de doble clic `build_buscar_chollos.bat`
  - Tras cada cambio funcional en `run_deals_gui.py`/`find_deals.py`/`amazon_service.py` hay que re-lanzar `pyinstaller BuscarChollos.spec --noconfirm` para que el `.exe` distribuido refleje el cambio (los `.py` no se copian automáticamente al build)
- Docker (despliega solo el servidor NAS, no las GUIs): `docker-compose -f deploy/docker-compose.yml up --build`

## Flujo de trabajo
1. Implementar
2. Añadir/actualizar tests
3. Ejecutar `pytest`
4. Solo entonces proponer commit

## Git (restricción dura)
- PROHIBIDO hacer `commit`/`push` sin permiso explícito
- Mensajes en español, claros (estilo en `git log`)
- Antes de commit: sugerir actualizar `context/` y documentación
- **Secretos estrictamente protegidos**: `.env` y sesiones `runtime/*.session` están ignorados en `.gitignore`. Nunca commitear credenciales reales; documentar nuevas variables en `.env.example`

## Estructura real (no romper límites)
- `src/domain/`: entidades y reglas puras (ProductInfo, CategoryCatalog, hashtag_rules)
- `src/use_cases/`: casos de uso; `ports/` define repositorios (category_repository, channel_history_reader) para inyectar en las integraciones
- `src/formatters/`: `telegram_formatter.py` (negritas, precios, emojis premium `<tg-emoji>`)
- `src/services/`: `amazon_service.py`, `publisher_service.py`
- `src/integrations/`: `amazon/` (PA-API + LWA), `openai/`, `telegram/`, `keepa/` (histórico de precios, API de pago), `storage/` (JSON en `data/`)
- `src/ui/`: Tkinter/ttkbootstrap — sin lógica de negocio
- `src/cli/`: utilidades (sync/migrate categorías, find_deals)
- `src/server/`: FastAPI para NAS
- `src/config/settings.py`: carga `.env` al importarse; acceder siempre vía `Config`, nunca hardcodear credenciales

## Puntos delicados
- Amazon Creators API v3.2 (LWA):
  - La API CAPA `itemCount` a 10 y `itemPage` a 10 (techo ~100 por query)
  - `find_deals` rota `SortBy` (5 estrategias) y deduplica por ASIN para ampliar cobertura (~200+ únicos)
  - Además del SortBy, hace un **barrido por marcas**: pide los refinements de la categoría (recurso `SearchItemsResource.SEARCHREFINEMENTS`) y busca las marcas top por separado. Si los refinements fallan, sigue sin abortar
  - `total_result_count` es **global/capeado** (mismo número para cualquier nodo): NO sirve para detectar cuándo cortar la paginación; solo se corta al llegar a una página vacía
  - ~1 petición/segundo o Amazon rechaza llamadas
  - No tocar autenticación LWA en `src/integrations/amazon/` sin validación
- La gráfica de histórico de precio en `deals_gui.py` se obtiene scrapeando Keepa con headers fijos (`KEEPA_HEADERS`)

## Convenciones no obvias
- Legibilidad: nombres largos > cortos
- Comentarios explican **por qué**, no qué
- UI: envolver llamadas a casos de uso en try/except con `messagebox` (evita que la app se cierre)
- Evitar lógica en UI → debe vivir en `use_cases`

## Estado actual (2026-08)
- Refactor del buscador de chollos COMPLETADO (sin commitear): `find_deals.py`, `deals_gui.py`, `amazon_service.py` y `amazon_api.py`
- `find_deals` ahora busca por SortBy rotado + **barrido por marcas de calidad**: usamos las marcas curadas del mapa marcas→categorías (`marcas_calidad.MARCAS_POR_CATEGORIA`) + las marcas de calidad que salgan en los refinements. Se ignoran las marcas genéricas chinas (BROTECT/MOKO...) que antes dominaban el barrido. `incluir_marcas=True` por defecto; `max_marcas=10`, `paginas_por_marca=2`. Paginación: solo se corta en página vacía (nunca por página corta)
- **Se pide a la API el descuento real** (`min_saving_percent`): por defecto el mismo `min_descuento` configurado (antes era 1, llenando el cupo de basura <15%). Configurable con `min_saving_percent_api`; el filtro local sigue como red de seguridad
- **Orden "calidad primero"**: `priorizar_marcas=True` (por defecto) ordena las marcas de calidad antes que el resto (a igual señal, mayor descuento). Con `False` vuelve al orden solo por descuento
- `CATEGORY_SEARCH_MAP` ampliado a **24 categorías tech** (se añadieron el 2026-08-29 vía sondeo en vivo `scripts/explore_search_nodes.py`): `software y suscripciones` (SearchIndex "Software", chollos 40%+ de Bitdefender/McAfee/MS), `smart home y domótica` ("Appliances" + keywords), `impresoras y consumibles` (keywords), `almacenamiento y discos` (keywords), `redes y wifi` (keywords). Las categorías pueden usar `keywords` además de `search_index`/`browse_node_id`
- `amazon_service.search_deals`/`get_brand_refinements` pasan `keywords` del config a la API; la API CAPA `itemCount` a 10 y `itemPage` a 10 (techo ~100 por query)
- `MARCAS_CALIDAD` ampliada y con normalización mejorada: match por nombre completo, sin sufijos, anterior a la coma y **primera palabra** (sub-marcas: "Logitech G", "Soundcore by Anker"). Cuidado: "Western Digital" se valida en cada paso antes de que el sufijo " digital" se lo coma
- Nuevo `scripts/test_busqueda_max_ofertas.py`: ejecuta el barrido (sin GUI) y exporta `data/max_ofertas_<fecha>.json`. Flags nuevos: `--api-min` (descuento a pedir a la API), `--sin-priorizar-marcas`, `--max-marcas` (por defecto 8). **Barrido completo 2026-08-01: 1360 ofertas únicas ≥15%** en `data/max_ofertas_20260801_122058.json`
- La GUI `deals_gui.py` tiene botón **"📂 Cargar resultados"** para abrir esos JSON y revisarlos (detalle + gráfica Keepa) sin volver a buscar
- Flujo preparado en la GUI para valorar con Keepa: botón **"⚡ Buscar TODOS los chollos"** (barrido completo + guarda JSON automáticamente) y panel **"Filtrado por Keepa"** con métricas configurables y botón "🎯 Filtrar por Keepa" (usa `FilterDealsKeepaUseCase`).
- **Filtrado Keepa IMPLEMENTADO pero DESACTIVADO por coste (2026-08-01)**: `FilterDealsKeepaUseCase` consulta el histórico de precios de Keepa (`src/integrations/keepa/keepa_client.py`, serie NEW→AMAZON, dominio es, últimos N días) y aplica reglas que detectan descuento real vs señuelo. La API es de pago (~60 €/mes con IVA) y queda fuera de presupuesto: el código está terminado y testeado, solo falta rellenar `KEEPA_API_KEY` en `.env` (placeholder ya añadido). Sin clave, devuelve la lista sin filtrar. Toda la documentación en `docs/KeepaImplementacion.md`. Detalles de la GUI en `docs/buscador_chollos.md` §"Flujo de valoración automática". Config: `KEEPA_API_KEY` en `.env` (~1 token/ASIN).
- `src/integrations/storage/deals_json.py` centraliza el formato JSON (`guardar_ofertas_json`/`productos_desde_json`): lo usan el script y la GUI
- **Filtro de calidad IMPLEMENTADO (gratuito, local, SOLO por marcas)**: `FilterChollosCalidadUseCase` (post-búsqueda, sin romper el barrido) descarta marcas no fiables según `MARCAS_CALIDAD` (`src/domain/marcas_calidad.py`; normaliza sufijos, cuidado: "Western Digital" se comprueba antes de quitar el sufijo " digital"). IMPORTANTE: la Amazon Creators API NO devuelve `customerReviews` (ni en search_items ni en get_items, verificado en vivo 2026-08-01) → `valoracion` es siempre None y no hay dato fiable para filtrar por estrellas; el criterio de valoración se descartó y se quitó `minReviewsRating` del pipeline. GUI: panel "⭐ Filtro de calidad" (checkbox "Solo marcas de calidad") + botones "⭐ Filtrar por calidad" y "🚀 Buscar TODOS y filtrar calidad". Script: flag `--marcas-calidad` (reflejado en metadatos del JSON). Docs: `docs/buscador_chollos.md` §"Filtro de calidad"
- `pytest` en verde (99 tests). Regla: si cambias el contrato de `find_deals`/`search_deals`, actualiza `test_find_deals.py` en el mismo cambio
- **Ejecutable BuscarChollos.exe creado (2026-08-03)**: nuevo spec `BuscarChollos.spec` (espejo de `PublicadorBuenChollo.spec`, apunta a `run_deals_gui.py`, icono `assets/logo.ico`; verificado: abre la GUI a la primera). Build: `pyinstaller BuscarChollos.spec --noconfirm` → `dist/BuscarChollos/BuscarChollos.exe`. Incluye `src`, `data`, `.env` y el logo. Tras cada cambio funcional en el buscador hay que re-lanzar el build

## Feature específica: run_deals_gui.py
- Valores por defecto centralizados como constantes en `src/ui/deals_gui.py`:
  - categorías: todas (`OPCION_TODAS`)
  - descuento: 15%–50% (`DESCUENTO_MINIMO/MAXIMO_PREDETERMINADO`)
  - cantidad: Max (`CANTIDAD_PREDETERMINADA`, "Max" = sin límite)
  - métricas Keepa provisionales: `KEEPA_AHORRO_VS_MEDIA_DEFECTO=10`, `KEEPA_MARGEN_SOBRE_MINIMO_DEFECTO=5`, `KEEPA_DIAS_HISTORIA_DEFECTO=90`
- Botón "⚡ Buscar TODOS los chollos": barrido completo (execute_todas, limite=None, incluir_marcas=True, priorizar_marcas=True) en hilo, guarda `data/max_ofertas_*.json` y muestra todo; el resultado queda en `self.chollos_brutos`
- La tabla tiene una columna **Marca**: las marcas de `MARCAS_CALIDAD` se marcan con ★ y en verde (escanear de un vistazo). `_poblar_tree` añade el tag "calidad"
- Botón "🎯 Filtrar por Keepa": aplica `FilterDealsKeepaUseCase.execute(chollos_brutos, config)` en hilo y reemplaza la tabla; "🚀 Buscar TODOS y filtrar" encadena ambos
- Panel "⭐ Filtro de calidad": `var_solo_marcas` (default True, checkbox "Solo marcas de calidad"). Botón "⭐ Filtrar por calidad": `calidad_use_case.execute(chollos_brutos, config)` en hilo (métodos `filtrar_por_calidad`/`_run_filtrar_calidad`/`_mostrar_calidad`); "🚀 Buscar TODOS y filtrar calidad" encadena barrido + filtro vía `start_buscar_todos(filtrar_calidad_despues=True)`
- Botón "📂 Cargar resultados": abre un `data/max_ofertas_*.json` del barrido y lo muestra en la tabla con su detalle/Keepa. Pruebas en `tests/unit/test_deals_gui.py`, `tests/unit/test_deals_json.py`, `tests/unit/test_filter_deals_keepa.py`
