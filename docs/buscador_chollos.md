# 🎯 Buscador de Chollos — Estrategia de Búsqueda

Este documento explica cómo el buscador de chollos (`run_deals_gui.py` →
`FindDealsUseCase`) maximiza el número de ofertas encontradas antes de decidir
si merece la pena valorarlas con Keepa.

## El problema: la API es muy limitada

La Amazon Creators API v3.2 (LWA) **capa** los resultados de búsqueda:

- `itemCount` está capeado a 10 (aunque la SDK documenta más).
- `itemPage` máximo es 10.
- ⇒ Techo por query: `10 × 10 = 100` ítems, y cada página se pide con una
  llamada aparte (~1 req/s o Amazon rechaza).

Además, `total_result_count` en la respuesta es **global/capeado**: devuelve el
mismo número (p. ej. `306`) tanto para un nodo de una categoría como para otro.
**No sirve para saber cuándo cortar la paginación.**

## La solución: dos barridos complementarios

### 1. Rotación de `SortBy` (cobertura base)

Cada criterio de ordenación devuelve un ranking distinto de la misma categoría,
con ofertas que no aparecen en los otros. `find_deals` rota 5 estrategias:

```python
_SORT_STRATEGIES = [
    None,                    # Featured (por defecto)
    "Price:LowToHigh",
    "Price:HighToLow",
    "NewestArrivals",
    "AvgCustomerReviews",
]
```

Por cada estrategia se piden páginas (1 a 10) hasta que llega una **página
vacía**. Ojo: una página corta (menos de 10 ítems) **no** corta el bucle, porque
Amazon a veces devuelve páginas cortas y aun así hay más resultados.

### 2. Barrido por marcas (cobertura de largo alcance)

Las ofertas de una marca popular pueden quedar fuera del ranking de los `SortBy`.
`find_deals` pide entonces los **refinements** de la categoría:

- Recurso `SearchItemsResource.SEARCHREFINEMENTS` (= `"searchRefinements"`).
- Dentro de `search_result.search_refinements.other_refinements` hay un
  refinement cuya `display_name` contiene "marca"/"marcas", con `bins` = marcas
  (ej. `['XIAOMI', 'Samsung', 'Google', 'SPC', 'Gigaset']`).

Con esas marcas se hacen búsquedas adicionales `brand=Xiaomi` (hasta
`max_marcas=10`, `paginas_por_marca=2` páginas por marca), deduplicando todo por
ASIN. Si los refinements fallan, el buscador **sigue sin abortar** (degrade
silencioso).

### 3. Descuento real pedido a la API (evitar llenar el cupo de ruido)

Los `SortBy` piden a Amazon `minSavingPercent` = **el descuento mínimo del
usuario** (antes era `1`, con lo que Amazon llenaba el cupo de 100/query con
ofertas de 1-14% que luego se descartaban en local). El filtro local sigue
como red de seguridad (la API "no respeta el umbral con exactitud").

Por defecto la API recibe `min_descuento`; se puede pedir un umbral distinto
con `min_saving_percent_api` (None = mismo que el filtro local).

### 4. Orden "calidad primero"

Con `priorizar_marcas=True` (valor por defecto) los resultados **no** se
ordenan solo por % de descuento: las ofertas de marcas de calidad van primero
y, dentro del mismo grupo, por descuento. Con `priorizar_marcas=False` se
vuelve al orden clásico solo por descuento.

### 5. Umbral de descuento a la API en las marcas

Igual que en el SortBy, el barrido por marcas también pide
`minSavingPercent = min_descuento` a la API (fr
ente a `1` antes).

Parámetros de `execute()`: `incluir_marcas=True` por defecto, `max_marcas=10`,
`paginas_por_marca=2`, `min_saving_percent_api=None`, `priorizar_marcas=True`.
`execute_todas()` propaga `incluir_marcas`, `min_saving_percent_api` y
`priorizar_marcas`.

## Categorías y nodos tech

`CATEGORY_SEARCH_MAP` en `src/domain/categories_search_index.py` mezcla:

- **`search_index`** (`Computers`, `VideoGames`, `Electronics`, `Software`,
  `Appliances`): cubren la categoría completa; `Electronics` es muy amplio y
  agrupa todo.
- **`browse_node_id`**: nodos tecnológicos concretos del árbol de Electrónica,
  **verificados en vivo el 2026-08-01** (ascendiendo ancestros desde resultados
  reales). Cada nodo devuelve un ranking de ofertas distinto, así que cuantos
  más nodos, más chollos únicos (el buscador deduplica por ASIN entre
  categorías).
- **`keywords`**: para nichos tech sin browse_node estable (o con el índice
  mezclado con papel/algo no-tech), se busca por palabra clave (ej. "router
  wifi", "disco duro"). Verificado en vivo el 2026-08-29 con
  `scripts/explore_search_nodes.py`.

El mapa tiene **24 categorías tech**: las 19 clásicas +
`software y suscripciones`, `smart home y domótica`, `impresoras y
consumibles`, `almacenamiento y discos` y `redes y wifi`.

Nodos verificados: Informática `683279031`, Tabletas `938010031`,
Comunicación móvil `665492031`, Wearables `17425674031`, Audio Hi-Fi
`665476031`, Audio portátil `665477031`, Auriculares `17420905031`,
TV/vídeo/home cinema `664659031`, Televisores `934359031`, Fotografía
`664660031`, GPS `664661031`, Alimentación `970144031`, Pilas/cargadores
`934120031`, eBooks `928457031`, Radiocomunicación `928459031`, Telefonía fija
`928458031`.

> Nota: `browseNodeId` **sí filtra** resultados por nodo (cada nodo devuelve
> ítems distintos), pero `total_result_count` no cambia entre nodos (es
> global), por lo que no se usa para cortar.

## Filtros de descuento (en local)

A la API se le pide `minSavingPercent = min_descuento` (el umbral real del
usuario, no 1) y, además, el filtro local de descuento se aplica **en local**
porque la API no respeta exactamente el umbral: se descartan productos sin
título/imagen, sin `descuento_porcentaje`, o fuera del rango
`[min_descuento, max_descuento]`.

Se puede pedir a la API un umbral distinto (más alto) vía
`min_saving_percent_api`: a más alto, menos llamadas devuelven ofertas
marginales y el cupo de 100/query se llena de ofertas de verdad.

## Coste en tiempo

Cada categoría con el barrido completo hace ~5 estrategias × N páginas + hasta
20 llamadas de marcas (10 marcas × 2 páginas), a 1 req/s. Buscar en "Todas"
(24 categorías) es una pasada larga; para usos puntuales conviene seleccionar
categorías concretas en el desplegable o usar el script con categorías
elegidas.

## Resultados acumulados sin volver a buscar

`scripts/test_busqueda_max_ofertas.py` ejecuta el mismo barrido sin GUI y
exporta un JSON con todas las ofertas únicas a `data/max_ofertas_<fecha>.json`
(incluye ASIN, título, marca, precios, descuento, valoración y URL, listo para
valorar con Keepa). Flags nuevos: `--api-min` (descuento pedido a la API),
`--sin-priorizar-marcas`, `--max-marcas` (por defecto 8).

Al final del barrido imprime la señal de calidad: cuántas ofertas son de
marcas de la lista `MARCAS_CALIDAD` (% respecto del total), para calibrar si
el resultado está encajando.

Barrido completo de referencia (2026-08-01): **1360 ofertas únicas ≥15%** en
`data/max_ofertas_20260801_122058.json` (138 ≥50%, 97 ≥40%, 245 ≥30%).

La GUI (`run_deals_gui.py`) tiene el botón **"📂 Cargar resultados"** para abrir
esos JSON y revisarlos en la tabla con su detalle y la gráfica Keepa, sin
volver a golpear la API de Amazon. La conversión del JSON a `ProductInfo` la
hace `productos_desde_json` y el guardado `guardar_ofertas_json`, ambos en
`src/integrations/storage/deals_json.py` (formato compartido entre script y GUI).

## Flujo de valoración automática

La GUI automatiza la revisión manual que se hacía con las gráficas de Keepa,
en dos etapas:

1. **Buscar todos**: botón **"⚡ Buscar TODOS los chollos"** → barrido completo
   de las 24 categorías tech (SortBy + marcas de calidad, sin límite, con orden
   "calidad primero" y umbral real pedido a la API), muestra los resultados y
   guarda automáticamente `data/max_ofertas_<fecha>.json`.
2. **Filtrar por Keepa**: panel **"Filtrado por Keepa"** con métricas
   configurables (ahorro vs media %, margen sobre mínimo histórico %, días de
   historia mínimos) y botón **"🎯 Filtrar por Keepa"** que aplica
   `FilterDealsKeepaUseCase` sobre `self.chollos_brutos` y muestra el listado
   final para revisarlo como hasta ahora (detalle + gráfica Keepa). El botón
   **"🚀 Buscar TODOS y filtrar"** encadena las dos etapas en un solo clic.

### Las reglas del filtro (cómo se decide si una oferta es real)

Para cada chollo se consulta a la API de datos de Keepa su histórico de precio
nuevo (`NEW`, o `AMAZON` si no hay) de los últimos N días (N = días de historia,
90 por defecto) en el dominio `es`, y se calculan métricas sobre la serie
(`src/domain/keepa_metrics.py`): mínimo/media del período, mediana reciente
(últimos 7 días) y previa, coeficiente de variación previo, pendiente de
regresión (tendencia) y nº de cambios de dirección (giros).

Pasa el filtro un chollo si **el precio actual está en el mínimo del período
(o casi)**, o **viene de un precio estable que baja de golpe**, o **la gráfica
tiene tendencia descendente**. Descartan en cualquier caso:

- **Gráfica "sonda"**: oscila constantemente (muchos giros) sin salir de un
  rango, simulando estar en oferta.
- **Bajada desde precio inflado**: el mínimo del período es ≥20% más barato que
  el precio actual, es decir, antes estuvo mucho más barato.
- **Historia insuficiente**: la serie no cubre al menos la mitad del período
  pedido (no hay base para juzgar la forma de la gráfica).
- **No superar `ahorro_vs_media`**: si se configura, el precio actual debe
  estar al menos ese % por debajo de la media del período (endurecedor).

La GUI solo expone tres umbrales (ahorro vs media, margen sobre mínimo y días
de historia); el resto usa los valores por defecto de `_CONFIG_DEFECTO` en
`src/use_cases/filter_deals_keepa.py` (bajada desde estable 15%, estabilidad
previa 10% CV, tendencia 15%, giros máx. 12, mínimo histórico previo 20%).

### Arquitectura (Clean Architecture)

- `src/domain/keepa_metrics.py` — métricas puras sobre la serie (sin I/O).
- `src/integrations/keepa/keepa_client.py` — fachada sobre la librería `keepa`
  (chunking de ASINs de 50, serie NEW→AMAZON, errores → `None` + log).
  Implementa el puerto `KeepaRepository`.
- `src/use_cases/ports/keepa_repository.py` — contrato inyectado por constructor.
- `src/use_cases/filter_deals_keepa.py` — orquesta y aplica las reglas.
- `Config.KEEPA_API_KEY` (variable `KEEPA_API_KEY` en `.env`). Sin clave, el
  filtro devuelve los chollos sin filtrar (no rompe el flujo).

> La API de datos de Keepa es de pago: cada consulta consume ~1 token por ASIN,
> así que una valoración completa del barrido (1360 chollos) cuesta ~1360
> tokens. `stats` no se usa: la forma de la gráfica requiere la serie completa.

## Filtro de calidad (marcas fiables)

La valoración por Keepa es de pago, y además la Amazon Creators API **no
devuelve la valoración de los productos** (el recurso `customerReviews` llega
siempre `null`, tanto en `search_items` como en `get_items`; verificado en vivo
el 2026-08-01). Por eso el filtro de calidad es **gratuito, local y SOLO por
marcas**:

- `FilterChollosCalidadUseCase` (nuevo, en `src/use_cases/filter_chollos_calidad.py`)
  descarta los chollos cuya marca no está en la lista curada `MARCAS_CALIDAD`
  (`src/domain/marcas_calidad.py`). Config por defecto: `solo_marcas_calidad: True`.

En la GUI: panel **"⭐ Filtro de calidad"** con la casilla "Solo marcas de
calidad" y los botones **"⭐ Filtrar por calidad"** (aplica sobre
`self.chollos_brutos`) y **"🚀 Buscar TODOS y filtrar calidad"** (barrido
completo + filtro en un clic). La lista de marcas se puede ampliar editando
`MARCAS_CALIDAD` (cada marca en minúsculas, sin sufijos).

En el script del barrido: `--marcas-calidad` (filtra por marcas tras el
barrido); queda reflejado en `metadatos` del JSON.

## Ejecutable (BuscarChollos.exe)

Para distribuir el buscador sin necesidad de Python, hay un spec de PyInstaller:

- Spec: `BuscarChollos.spec` (espejo de `PublicadorBuenChollo.spec`).
- Entrada: `run_deals_gui.py`; nombre del exe `BuscarChollos`; icono
  `assets/logo.ico`; `console=False` (sin ventana de terminal).
- Build: `pyinstaller BuscarChollos.spec --noconfirm` →
  `dist/BuscarChollos/BuscarChollos.exe`.
- El build incluye `src`, `data` (JSONs de chollos), `.env` y el logo. El spec
  asume Python 3.14 con site-packages en `%LOCALAPPDATA%\Programs\Python\Python314`.
- **Importante**: tras cada cambio funcional en el buscador
  (`run_deals_gui.py`, `find_deals.py`, `amazon_service.py`, `deals_gui.py`) hay
  que re-lanzar el build; los `.py` no se copian solos al `.exe`.
