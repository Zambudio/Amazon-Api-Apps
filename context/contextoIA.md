# 🧠 Contexto del Proyecto: Publicador BuenChollo

Este archivo sirve como base de conocimiento principal para cualquier IA o agente que trabaje en este repositorio.

## 🚀 Resumen del Proyecto
**Publicador BuenChollo** es una solución integral para automatizar la publicación de ofertas de Amazon en canales de Telegram. Su objetivo es transformar un simple enlace de producto en un post de venta atractivo, enriquecido por IA (GPT) y con formato visual premium (emojis animados).

El sistema tiene dos modos de operación:
1.  **GUI (Desktop):** Aplicación Windows para gestión manual y visual de posts.
2.  **Server (NAS/Synology):** API FastAPI para ejecución autónoma y programada desde servidores.

## 🛠️ Tecnologías Clave
- **Lenguaje:** Python 3.11+
- **Interfaz:** `ttkbootstrap` (Tkinter moderno) para la GUI, `FastAPI` para el servidor.
- **APIs Externas:** 
    - Amazon Creators API v3.2 (LWA).
    - OpenAI API (GPT-4o/GPT-3.5-turbo) para síntesis de textos y categorización.
    - Telegram Bot API & Telethon (para lectura de histórico).
- **Persistencia:** Almacenamiento basado en JSON para categorías y reglas de hashtags.

## 📂 Estructura del Proyecto (Limpia)
- `src/`: Código fuente (Lógica de negocio, UI, Integraciones).
- `docs/`: Documentación del proyecto (README, mandatos de la IA).
- `AGENTS.md`: Manual operativo técnico para agentes de IA (Raíz).
- `deploy/`: Archivos de Docker, NAS y requisitos de servidor.
- `assets/`: Recursos visuales (Logos, iconos).
- `data/`: Bases de datos JSON y catálogos.
- `scripts/`: Utilidades de mantenimiento y migración.
- `runtime/`: Archivos temporales, logs y sesiones.
- `context/`: Archivos específicos para el contexto de la IA.

## ⚠️ INSTRUCCIÓN CRÍTICA PARA AGENTES ⚠️
> [!IMPORTANT]
> **Antes de realizar cualquier commit**, el agente DEBE sugerir al usuario la actualización de los archivos de la carpeta `@context/`. Esto garantiza que la documentación de contexto evolucione junto con el código y que futuros agentes tengan siempre la información más reciente.

## 📝 Instrucciones Generales para la IA
1.  **Idiomatic Python:** Seguir PEP 8. Usar Type Hints siempre que sea posible.
2.  **Desacoplamiento:** No mezclar lógica de Telegram o Amazon directamente en la UI. Usar siempre los `use_cases`.
3.  **Seguridad:** NUNCA hardcodear credenciales. Usar el archivo `.env` mediante `src/config/settings.py`.
4.  **Validación:** Antes de proponer cambios, verificar el impacto en el flujo `Amazon -> GPT -> Telegram Formatter`.

## 🛒 Configuración inicial del Buscador de Chollos
La GUI `run_deals_gui.py` arranca buscando en todas las categorías, con un rango de descuento del 15 % al 50 % y sin límite de cantidad (`Max`). Los valores se centralizan como constantes en `src/ui/deals_gui.py`.

## 🎯 Buscador de Chollos — Cómo maximiza las ofertas (2026-08)
- **Doble barrido en `FindDealsUseCase.execute`** (`src/use_cases/find_deals.py`):
  1. **Rotación de `SortBy`** (5 estrategias: Featured, Precio ↑/↓, Novedades, Valoración): cada una devuelve un ranking distinto; se deduplica por ASIN.
  2. **Barrido por marcas de calidad** (`incluir_marcas=True`): usa las marcas curadas del mapa `marcas_calidad.MARCAS_POR_CATEGORIA` (marcas→categorías) + las marcas de calidad de los refinements de la categoría. Se **ignoran las genéricas** (BROTECT/MOKO...) que dominaban el barrido. Por defecto `max_marcas=10`, `paginas_por_marca=2`. Si los refinements fallan, sigue sin abortar.
- **Se pide a la API el descuento real:** `minSavingPercent = min_descuento` (antes `1`, que llenaba el cupo de ofertas de 1-14%). Configurable con `min_saving_percent_api`; el filtro local sigue como red de seguridad.
- **Orden "calidad primero":** `priorizar_marcas=True` (default) ordena las marcas de calidad antes que el resto (a igual señal, mayor descuento). Con `False`, orden clásico solo por descuento.
- **Paginación:** `itemCount` y `itemPage` están capeados a 10 (techo ~100/query). Solo se corta al llegar a una **página vacía** (una página corta NO corta). `total_result_count` es global/capeado → NO se usa para cortar.
- **Categorías (24):** `CATEGORY_SEARCH_MAP` combina `search_index` (`Computers`, `VideoGames`, `Electronics`, + `Software`, `Appliances`), 13+ nodos tech `browse_node_id` verificados en vivo (2026-08-01) y **`keywords`** (niches sin browse_node: vér 2026-08-29). Nuevas categorías: software y suscripciones, smart home y domótica, impresoras y consumibles, almacenamiento y discos, redes y wifi.
- **API/fachadas:** `search_products`/`search_deals` aceptan `brand` y `keywords`; `get_brand_refinements(categoria, keywords)`. Los refinements viven en `search_refinements.other_refinements` (refinement con display_name que contiene "marca").
- **Detalle técnico:** en la SDK el recurso de refinements se llama `SearchItemsResource.SEARCHREFINEMENTS` (sin guion bajo), valor `"searchRefinements"`.
- **Barrido sin GUI:** `scripts/test_busqueda_max_ofertas.py` exporta todas las ofertas únicas a `data/max_ofertas_<fecha>.json`; flags `--api-min` y `--sin-priorizar-marcas`. Barrido completo 2026-08-01 → **1360 ofertas únicas ≥15%** (`data/max_ofertas_20260801_122058.json`).
- **Ver resultados en GUI:** botón **"📂 Cargar resultados"** en `run_deals_gui.py` abre esos JSON (función `productos_desde_json`) y los muestra en la tabla con detalle + gráfica Keepa, sin volver a buscar.
- **Flujo de valoración Keepa (IMPLEMENTADO 2026-08-01, DESACTIVADO por coste):** la GUI tiene **"⚡ Buscar TODOS los chollos"** (barrido completo + guarda JSON automático) y panel **"Filtrado por Keepa"** con métricas configurables + botón **"🎯 Filtrar por Keepa"**. `FilterDealsKeepaUseCase` consulta el histórico de precios de Keepa y aplica reglas: pasa si el precio está en el mínimo del período, o cae desde un precio estable, o hay tendencia descendente; descarta "sondas" (oscilación constante) y bajadas desde precio inflado (mínimo previo ≥20% más barato). La API de datos de Keepa es de pago (~60 €/mes con IVA) y está fuera de presupuesto: el código está listo y solo falta `KEEPA_API_KEY` en `.env` (placeholder ya añadido); sin clave devuelve la lista sin filtrar. Reglas y umbrales en `_CONFIG_DEFECTO` de `src/use_cases/filter_deals_keepa.py`; métricas puras en `src/domain/keepa_metrics.py`; cliente+adapter en `src/integrations/keepa/keepa_client.py`; puerto `src/use_cases/ports/keepa_repository.py`. Documentación completa: `docs/KeepaImplementacion.md`.
- **Formato JSON compartido:** `src/integrations/storage/deals_json.py` (`guardar_ofertas_json`/`productos_desde_json`) lo usan el script y la GUI para no duplicar formatos.
- **Filtro de calidad (IMPLEMENTADO 2026-08-01, gratuito/local, SOLO por marcas):** la Amazon Creators API NO devuelve `customerReviews` (ni search_items ni get_items; verificado en vivo) → `valoracion` siempre None, se descartó el criterio de estrellas. `FilterChollosCalidadUseCase` (`src/use_cases/filter_chollos_calidad.py`) descarta marcas que no están en `MARCAS_CALIDAD` (`src/domain/marcas_calidad.py`, lista curada de marcas tech fiables; normaliza sufijos — cuidado: "Western Digital" se comprueba antes de quitar el sufijo " digital"). GUI: panel **"⭐ Filtro de calidad"** (checkbox "Solo marcas de calidad") y botones **"⭐ Filtrar por calidad"** / **"🚀 Buscar TODOS y filtrar calidad"**. Script: `--marcas-calidad` (en metadatos del JSON).
- **Ejecutable BuscarChollos.exe (2026-08-03):** spec `BuscarChollos.spec` (espejo de `PublicadorBuenChollo.spec`), entrada `run_deals_gui.py`, icono `assets/logo.ico`, `console=False`. Build: `pyinstaller BuscarChollos.spec --noconfirm` → `dist/BuscarChollos/BuscarChollos.exe`. Incluye `src`, `data`, `.env` y el logo. Verificado: abre la GUI a la primera. ⚠️ Tras cada cambio funcional en el buscador (`run_deals_gui.py`, `deals_gui.py`, `find_deals.py`, `amazon_service.py`) hay que re-lanzar el build; los `.py` no se copian solos al `.exe`.
- Detalles completos en `docs/buscador_chollos.md`.

## 📚 Documentación de referencia (completa, 2026-09)
- `README.md` (raíz) — visión general, instalación, uso, testing, empaquetado y despliegue.
- `docs/ARQUITECTURA.md` — capas, módulos, responsabilidades y reglas de diseño.
- `docs/FUNCIONALIDAD.md` — funcionalidad detallada de las dos GUIs, la API NAS y los scripts.
- `docs/DESARROLLO.md` — convenciones de código, testing, PyInstaller, Docker y puntos delicados.
- `docs/buscador_chollos.md` — estrategia detallada del buscador (barrido, marcas, umbral API).
- `docs/KeepaImplementacion.md` — implementación del filtrado Keepa.
- `context/arquitectura.md` — flujos técnicos y estructura por capas.
