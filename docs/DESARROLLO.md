# Desarrollo

Guía de desarrollo, testing, empaquetado y puntos delicados de **Amazon-Api-Apps**.

---

## 1. Entorno

- **Python 3.14** (build EXE) o **3.11+** (ejecución y tests).
- Virtualenv en `.venv/`.
- Dependencias en `requirements.txt`.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 2. Convenciones de código

- **Cada `.py` empieza con un docstring de cabecera** explicando qué hace y su contexto.
- **Legibilidad**: nombres largos > cortos (`min_saving_percent_api` antes que `ms`).
- **Comentarios explican el *por qué***, no el qué.
- **Prohibido `print()`**: usar `logging` (`logger = logging.getLogger(__name__)`).
- **Clean Architecture estricta**: no cruzar capas (ver `docs/ARQUITECTURA.md`).
- **UI**: envolver llamadas a casos de uso en `try/except` con `messagebox` para que la app no se cierre.
- **Evitar lógica en UI**: debe vivir en `use_cases`.

---

## 3. Testing

```powershell
pytest                      # Suite completa
pytest tests/unit -q        # Lógica pura
pytest tests/integration -q # Flujos de casos de uso
```

### Estructura

| Carpeta | Contenido |
|---|---|
| `tests/unit/` | Lógica pura: formateadores, normalización de marcas, filtros, Keepa, Amazon API (mocks). |
| `tests/integration/` | Flujo completo de casos de uso (catálogo, generación de posts). |

### Reglas

- Toda funcionalidad nueva o modificada ⇒ **tests obligatorios**.
- Si cambias el contrato de `find_deals` / `search_deals`, actualiza `test_find_deals.py` **en el mismo cambio**.

**Flujo de trabajo:**
1. Implementar.
2. Añadir/actualizar tests.
3. Ejecutar `pytest` (debe quedar todo en verde).
4. Solo entonces proponer commit.

---

## 4. Empaquetado (PyInstaller)

Los `.spec` asumen **Python 3.14** con site-packages en `%LOCALAPPDATA%\Programs\Python\Python314`.

### Buscador de chollos

```powershell
pyinstaller BuscarChollos.spec --noconfirm
# → dist/BuscarChollos/BuscarChollos.exe
```

Existe también `build_buscar_chollos.bat` para doble clic.

> ⚠️ **Tras cada cambio funcional** en `run_deals_gui.py`, `find_deals.py`, `amazon_service.py` o `amazon_api.py` hay que **re-lanzar el build**: los `.py` no se copian automáticamente al `.exe` distribuido.

### Publicador de ofertas

```powershell
pyinstaller PublicadorBuenChollo.spec --noconfirm
# → dist/PublicadorBuenChollo/PublicadorBuenChollo.exe
```

El `.exe` incluye `src`, `data`, `.env` y el logo (`assets/logo.ico`).

---

## 5. Despliegue NAS (Docker)

Solo el servidor NAS (no las GUIs).

```powershell
docker-compose -f deploy/docker-compose.yml up --build
```

- `deploy/Dockerfile.nas`: `python:3.11-slim` + `requirements_server.txt` + arranque de uvicorn en `:8000`.
- `deploy/docker-compose.yml`: servicio `buenchollo-scheduler`, volumen `nas_data`, `TZ=Europe/Madrid`.
- Guía Synology: `deploy/GUIA_SYNOLOGY.md`.

---

## 6. Puntos delicados

### 6.1 Amazon Creators API v3.2 (LWA)

- La API **CAPA** `itemCount` a 10 y `itemPage` a 10 (techo ~100 por query).
- `find_deals` rota `SortBy` (5 estrategias) y deduplica por ASIN para ampliar cobertura (~200+ únicos).
- Hace un **barrido por marcas de calidad**: pide los refinements de la categoría
  (`SearchItemsResource.SEARCHREFINEMENTS`) y busca las marcas curadas por separado.
  Si los refinements fallan, sigue sin abortar.
- `total_result_count` es **global/capeado** (mismo número para cualquier nodo):
  **NO** sirve para detectar cuándo cortar la paginación; solo se corta al llegar a una página vacía.
- ~1 petición/segundo o Amazon rechaza llamadas.
- **No tocar autenticación LWA** en `src/integrations/amazon/` sin validación.

### 6.2 Normalización de marcas

En `src/domain/marcas_calidad.py`:

- Match por nombre completo, sin sufijos legales, anterior a la coma y **primera palabra**.
- Sub-marcas: "Logitech G", "Soundcore by Anker".
- ⚠️ **"Western Digital" se valida en cada paso antes de que el sufijo " digital" se lo coma.**

### 6.3 Gráfica de histórico de precios

En `deals_gui.py` se obtiene scrapeando Keepa con **headers fijos** (`KEEPA_HEADERS`):
`https://graph.keepa.com/pricehistory.png?asin={asin}&domain=es`

Cada descarga va en su propio hilo; `_set_label_image` comprueba que el producto
siga siendo el seleccionado antes de pintar (evita que una descarga lenta pise
la imagen del producto actual).

### 6.4 Filtrado Keepa (coste)

`FilterDealsKeepaUseCase` está **terminado y testeado** pero **desactivado por coste**
(API de pago ~60 €/mes). Solo falta rellenar `KEEPA_API_KEY` en `.env`.
Sin clave, devuelve la lista sin filtrar. Documentación: `docs/KeepaImplementacion.md`.

### 6.5 Amazon no devuelve valoraciones

La Creators API **no** devuelve `customerReviews` (ni en search ni en get, verificado en vivo 2026-08-01).
`valoracion` es siempre `None`; el criterio de valoración se descartó del pipeline.

---

## 7. Reglas de Git y Seguridad

- **PROHIBIDO hacer `commit` / `push` sin permiso explícito.**
- Mensajes en **español**, claros y concisos (ver estilo en `git log`).
- Antes de commit: sugerir actualizar `context/` y documentación.
- **Gestión estricta de secretos**:
  - El archivo `.env` y las sesiones de usuario (`runtime/*.session`) están estrictamente ignorados en `.gitignore`.
  - NUNCA commitear archivos `.env` reales, tokens, claves privadas o volcados de datos locales.
  - Toda nueva variable de configuración debe documentarse en `.env.example`.

---

## 8. Regla triple de doc

Cada cambio funcional debe actualizar **tres sitios**:

1. `AGENTS.md` (guía operativa de alta señal).
2. `docs/` (documentación detallada: `ARQUITECTURA.md`, `FUNCIONALIDAD.md`, `DESARROLLO.md`, `buscador_chollos.md`, ...).
3. `context/` (`contextoIA.md`, `arquitectura.md`, `instrucciones_ia.md`).