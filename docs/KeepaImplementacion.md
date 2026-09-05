# 🔍 Keepa — Valoración automática de chollos (implementación)

> **Estado (2026-08-01): IMPLEMENTADO pero DESACTIVADO por coste.** La API de
> datos de Keepa es de pago (~60 €/mes con IVA) y de momento queda fuera de
> presupuesto. Todo el código está terminado, testeado y commiteado; solo hay
> que añadir `KEEPA_API_KEY` al `.env` para activarlo.

Este documento explica qué se ha implementado para valorar automáticamente si
un chollo de Amazon tiene un **descuento real** usando el histórico de precios
de Keepa, y cómo se reactivará cuando haya presupuesto.

---

## 1. Qué resuelve

Antes, la decisión de "¿este chollo es bueno?" se tomaba a mano: se abría la
gráfica de Keepa de cada producto y se juzgaba su forma. El filtro automatiza
esa revisión convirtiendo la "forma de la gráfica" en métricas y reglas
numéricas:

- **Pasa** (descuento real) si el precio actual:
  - está **en el mínimo** del período (o casi), **o**
  - viene de un **precio estable que baja de golpe**, **o**
  - tiene **tendencia descendente** (la gráfica va bajando).
- **Descarta** (señuelo) si:
  - la gráfica es una **"sonda"**: sube y baja constantemente sin salir de un
    rango, simulando estar en oferta, **o**
  - ha hecho una **bajada desde un precio inflado**: el mínimo del período es
    ≥20% más barato que el precio actual (antes estuvo mucho más barato), **o**
  - la **historia es insuficiente**: la serie no cubre al menos la mitad del
    período pedido (no hay base para juzgar la forma), **o**
  - no supera el endurecedor `ahorro_vs_media` si está configurado.

## 2. Cómo se obtienen los datos (API de Keepa)

Se usa la librería Python `keepa` (ya en `requirements.txt`). La llamada clave:

```python
api.query(asins, domain="es", history=True, days=90, progress_bar=False)
```

- `domain="es"` → histórico de Amazon España.
- `history=True` + `days=90` → la **serie completa** de precios de los últimos
  90 días (no basta `stats`: la forma de la gráfica necesita la serie).
- Se usa la serie **NEW** (precio nuevo más bajo del marketplace, incluye a
  Amazon cuando es el más barato), con **fallback a AMAZON** si NEW no existe.
- Los puntos sin oferta (NaN / -1) se descartan.
- **Coste: ~1 token por ASIN.** Un barrido completo de 1360 chollos ≈ 1360
  tokens. La librería espera tokens automáticamente (`wait=True` por defecto).

## 3. Arquitectura (Clean Architecture)

| Capa | Archivo | Responsabilidad |
|---|---|---|
| `domain` | `src/domain/keepa_metrics.py` | Métricas puras sobre la serie: mínimo/media/medianas, coeficiente de variación (estabilidad), pendiente de tendencia, nº de giros (sonda). Sin I/O. |
| `integrations` | `src/integrations/keepa/keepa_client.py` | Fachada sobre la librería `keepa`: chunking de ASINs (50 por lote, la librería limita a 100), serie NEW→AMAZON, errores → `None` + log. Implementa el puerto. |
| `use_cases/ports` | `src/use_cases/ports/keepa_repository.py` | Contrato `obtener_historial(asins, dias)` que se inyecta por constructor. |
| `use_cases` | `src/use_cases/filter_deals_keepa.py` | Orquesta: consulta histórico, calcula métricas y aplica las reglas. |
| `config` | `src/config/settings.py` | `Config.KEEPA_API_KEY` (variable `KEEPA_API_KEY` en `.env`). |

Flujo del botón **"🎯 Filtrar por Keepa"** de `run_deals_gui.py`:

```
chollos_brutos ──> FilterDealsKeepaUseCase.execute(chollos, config)
                        │
                        ├─ KeepaRepository.obtener_historial(asins, dias=90)
                        ├─ calcular_metricas(serie)        (por ASIN)
                        ├─ _cumple_reglas(metricas, config)
                        └─ lista filtrada ──> se muestra en la tabla
```

## 4. Las reglas y sus umbrales

La GUI solo expone tres campos (ahorro vs media %, margen sobre mínimo % y
días de historia). El resto usa los valores por defecto de `_CONFIG_DEFECTO`
en `src/use_cases/filter_deals_keepa.py`:

| Config | Defecto | Significado |
|---|---|---|
| `dias_historia` | 90 | Ventana a consultar. Se exige al menos el 50% de historia para juzgar la forma. |
| `margen_sobre_minimo` | 5 | % sobre el mínimo del período para considerarlo "en el mínimo". |
| `ahorro_vs_media` | 10 | Endurecedor: % mínimo bajo la media del período. `0` = desactivado. |
| `bajada_reciente_pct` | 15 | % de caída de la mediana reciente (7 días) frente a la previa. |
| `estabilidad_previo_pct` | 10 | CV máx. del período previo para la regla "estable → baja". |
| `tendencia_descendente_pct` | 15 | % de descenso total de la pendiente en la ventana. |
| `sonde_giros_max` | 12 | Más giros (cambios de dirección) = sonda → descartar. |
| `historico_anterior_pct` | 20 | Si el mínimo del período es ≥X% más barato que el actual → descartar. |

Lógica:

```
PASA = (cerca_minimo OR caida_desde_estable OR tendencia_descendente)
       AND NOT sonda
       AND NOT antes_mucho_más_barato
       AND (ahorro_vs_media == 0 OR precio bajo la media ese %)
```

Sin `KEEPA_API_KEY` (o si la consulta falla), `execute` devuelve la lista sin
filtrar para no romper el flujo de la GUI.

## 5. Cómo se reactiva cuando haya presupuesto

1. Suscribirse a la API de datos de Keepa (https://get.keepa.com).
2. En `.env`, rellenar la línea (ya existe como placeholder):
   ```
   KEEPA_API_KEY=la_clave_real
   ```
3. Abrir `run_deals_gui.py` y usar **"⚡ Buscar TODOS los chollos"** y luego
   **"🎯 Filtrar por Keepa"** (o directamente **"🚀 Buscar TODOS y filtrar"**).
4. El resultado se muestra en la tabla; al seleccionar un producto se sigue
   viendo su detalle y su gráfica de Keepa para la revisión final.

> [!NOTE]
> Configura `KEEPA_API_KEY` en tu `.env` local basándote en `.env.example`.
> Mantén siempre tus credenciales protegidas fuera del control de versiones.

## 6. Tests

- `tests/unit/test_keepa_metrics.py` — métricas puras (limpieza de serie,
  estadísticas, tendencia, giros).
- `tests/unit/test_filter_deals_keepa.py` — reglas con repositorio falso:
  mínimo real pasa, sonda se descarta, bajada desde inflado se descarta, etc.
- `tests/unit/test_keepa_client.py` — chunking, fallback NEW→AMAZON, errores
  → `None`, sin clave → no disponible.

Ejecutar: `pytest tests/unit -q` (el filtro no toca la red: se inyecta un
repositorio falso en los tests).
