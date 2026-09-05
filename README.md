# Amazon-Api-Apps 🚀

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Architecture](https://img.shields.io/badge/architecture-Clean%20Architecture-success.svg)](#arquitectura)
[![Tests](https://img.shields.io/badge/tests-99%20passed-brightgreen.svg)](#testing)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Tkinter](https://img.shields.io/badge/GUI-ttkbootstrap-orange.svg)](#aplicaciones)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-Production%20Ready-green.svg)](#)

> **Suite profesional y modular para la búsqueda algorítmica de chollos en Amazon, validación de descuentos reales, generación de contenido enriquecido con Inteligencia Artificial (OpenAI) y publicación automatizada en canales de Telegram.**

Desarrollado bajo principios estrictos de **Clean Architecture**, desacoplamiento de capas y cobertura completa de pruebas automatizadas. Incluye aplicaciones de escritorio nativas (GUI), servidor REST para despliegue en NAS / Docker y herramientas avanzadas de línea de comandos.

---

## 📑 Tabla de Contenidos

- [Visión General](#visión-general)
- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Aplicaciones del Ecosistema](#aplicaciones-del-ecosistema)
  - [1. Buscador de Chollos (run_deals_gui.py)](#1-buscador-de-chollos-desktop-gui)
  - [2. Publicador BuenChollo (run_gui.py)](#2-publicador-buenchollo-desktop-gui)
  - [3. Servidor REST Headless (FastAPI)](#3-servidor-rest-headless-fastapi)
  - [4. Scripts y CLI de Automatización](#4-scripts-y-cli-de-automatización)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Requisitos Previos](#requisitos-previos)
- [Instalación y Puesta en Marcha](#instalación-y-puesta-en-marcha)
- [Configuración de Entorno (.env)](#configuración-de-entorno-env)
- [Guía de Uso Rápido](#guía-de-uso-rápido)
- [Compilación a Ejecutables Windows (.exe)](#compilación-a-ejecutables-windows-exe)
- [Despliegue con Docker (NAS / Servidor)](#despliegue-con-docker-nas--servidor)
- [Testing y Calidad de Código](#testing-y-calidad-de-código)
- [Seguridad y Buenas Prácticas](#seguridad-y-buenas-prácticas)
- [Documentación Adicional](#documentación-adicional)
- [Licencia](#licencia)

---

## 🌟 Visión General

El ecosistema **Amazon-Api-Apps** resuelve el flujo completo de curación de ofertas de comercio electrónico:

```
┌─────────────────┐       ┌──────────────────────┐       ┌──────────────────┐       ┌─────────────────────┐
│  Amazon PA-API  │ ────> │ Algoritmo de Calidad │ ────> │ Enriquecimiento  │ ────> │     Publicación     │
│   Creators v3.2 │       │   y Descuento Real   │       │   Copy con IA    │       │  Telegram Premium   │
│   (LWA OAuth)   │       │   (Keepa + Marcas)   │       │  (OpenAI GPT-4o) │       │   (<tg-emoji> + UI) │
└─────────────────┘       └──────────────────────┘       └──────────────────┘       └─────────────────────┘
```

1. **Extracción Exhaustiva:** Integración con la nueva **Amazon Creators API v3.2** mediante autenticación segura **Login with Amazon (LWA)**, rotación de 5 estrategias de ordenación (`SortBy`) y barrido segmentado por marcas.
2. **Filtrado Inteligente:** Motor de evaluación de ofertas que distingue descuentos reales de señuelos comerciales, prioriza marcas reconocidas y coteja el historial de precios con Keepa.
3. **Copywriting Persuasivo:** Síntesis y redacción automática con modelos de lenguaje de OpenAI (GPT-4o / GPT-4o-mini), generando textos de venta directos y concisos.
4. **Formateo Visual de Alta Gama:** Generador de posts para Telegram con soporte de emojis animados premium (`<tg-emoji>`), carrusel de fotografías del producto y gestión de hashtags por categoría.

---

## 🏛️ Arquitectura del Sistema

El proyecto sigue rigurosamente los principios de **Clean Architecture**. La regla de oro: **las dependencias siempre apuntan hacia el interior**, aislando el núcleo de negocio de cualquier detalle de infraestructura, framework o servicio externo.

```
                  ┌──────────────────────────────────────────────────┐
                  │                 Presentación / UI                │
                  │   deals_gui.py · main_gui.py · nas_api (FastAPI) │
                  └─────────────────────────┬────────────────────────┘
                                            │
                                            ▼
                  ┌──────────────────────────────────────────────────┐
                  │              Casos de Uso (Use Cases)            │
                  │  find_deals · generate_post · filter_deals_keepa │
                  │      filter_chollos_calidad · ports/ (interfaces)│
                  └─────────────────────────┬────────────────────────┘
                                            │
                                            ▼
                  ┌──────────────────────────────────────────────────┐
                  │                   Dominio Puro                   │
                  │    entities · categories_search_index · marcas   │
                  │            keepa_metrics · hashtag_rules         │
                  └──────────────────────────────────────────────────┘
                                            ▲
                                            │ (Implementan puertos)
                  ┌─────────────────────────┴────────────────────────┐
                  │           Infraestructura & Integraciones        │
                  │   Amazon PA-API/LWA · OpenAI · Keepa · Telethon  │
                  │        Telegram Bot API · JSON Repositories      │
                  └──────────────────────────────────────────────────┘
```

### Reglas Críticas de Aislamiento

- **`src/domain/`**: Entidades y reglas matemáticas/lógicas puras. Cero operaciones de I/O, sin dependencias de red, base de datos ni librerías externas.
- **`src/use_cases/`**: Orquestación de flujos de negocio. Reciben servicios e integraciones mediante **Inyección de Dependencias (DI)** a través de interfaces (`ports/`).
- **`src/services/`**: Fachadas internas de aplicación que coordinan llamadas de integraciones.
- **`src/integrations/`**: Adaptadores para APIs externas (Amazon, Telegram, OpenAI, Keepa, Storage). Capturan excepciones de red y devuelven tipos de dominio normalizados o `None` con trazabilidad vía `logging`.
- **`src/formatters/`**: Transformación de texto y diseño visual (HTML de Telegram, porcentajes, precios, etiquetas).
- **`src/ui/`**: Interfaces gráficas (Tkinter/ttkbootstrap). **Sin lógica de negocio**: delegan exclusivamente en los casos de uso.
- **`src/config/`**: Centralización de configuración a través de la clase `Config` con validación en tiempo de ejecución (`settings.py`).

---

## 💻 Aplicaciones del Ecosistema

| Componente | Tipo | Punto de Entrada | Propósito Principal |
|---|---|---|---|
| **Buscador de Chollos** | Desktop GUI | `python run_deals_gui.py` | Exploración masiva, filtrado y detección de ofertas sin publicar. |
| **Publicador BuenChollo** | Desktop GUI | `python run_gui.py` | Enriquecimiento con IA, previsualización y publicación directa en Telegram. |
| **API Servidor NAS** | REST API | `uvicorn src.server.nas_api:app` | Microservicio FastAPI para automatizaciones programadas en NAS/Docker. |
| **Barrido Batch** | CLI Script | `python scripts/test_busqueda_max_ofertas.py` | Extracción desatendida de miles de ofertas con exportación a JSON. |

---

### 1. Buscador de Chollos (Desktop GUI)

Herramienta analítica de consulta interactiva para monitorizar las mejores ofertas del mercado español:

- **24 Categorías de Tecnología:** Sondeadas e indexadas en vivo (`Informática`, `Smart Home`, `Smartphones`, `Componentes`, `Audio`, `Gaming`, `Redes y Wi-Fi`, `Almacenamiento`, etc.).
- **Algoritmo de Doble Barrido:**
  - *Barrido A (SortBy Rotativo):* Rota por 5 criterios de ordenación (`Relevance`, `PriceLowToHigh`, `PriceHighToLow`, etc.) superando los límites habituales de paginación de la API.
  - *Barrido B (Marcas Curadas):* Barrido por marcas confiables extraídas de refinamientos y del catálogo curado `MARCAS_CALIDAD`.
- **Detección de Ofertas Flash:** Identifica promociones con límite temporal y calcula la fecha exacta de expiración.
- **Gráficas de Histórico de Precios:** Renderiza la curva histórica de precios de Keepa para auditoría visual directa.
- **Filtrado Avanzado:**
  - `⭐ Filtro de Calidad`: Limpia marcas blancas genéricas irrelevantes de un clic.
  - `🎯 Filtrado Keepa`: Análisis algorítmico de precio medio de 90 días vs precio actual.
- **Exportación / Importación:** Guarda y recupera volcados JSON completos para análisis diferido sin consumir cuota de API.

---

### 2. Publicador BuenChollo (Desktop GUI)

Estación de trabajo para editores de contenido de ofertas:

- **Ingesta Rápida:** Pega cualquier enlace de Amazon (estándar, corto `amzn.to` o ASIN) y extrae de inmediato especificaciones, precio anterior, precio de oferta y porcentaje de rebaja.
- **Redacción Asistida con IA:** Conexión con GPT-4o para resumir fichas técnicas aburridas en copys persuasivos de 2-3 líneas listos para vender.
- **Gestor Visual de Medios:** Carrusel de hasta 7 imágenes del producto de alta resolución con selector o subida de capturas personalizadas.
- **Catalogación Inteligente:** Detección y asignación automática de hashtags según el catálogo de categorías sincronizado.
- **Envío en 1 Clic:** Publica inmediatamente la composición (imagen + texto estilizado + enlace de afiliado) en el canal de administración o en el canal público.

---

### 3. Servidor REST Headless (FastAPI)

Diseñado para ejecutarse de forma continua en un contenedor Docker sobre un NAS (Synology, QNAP, TrueNAS o VPS Linux):

- Expone endpoints para programar extracciones periódicas.
- Desacoplado de la interfaz gráfica: consume los mismos casos de uso del dominio.
- Arquitectura ligera con imagen base `python:3.11-slim`.

---

### 4. Scripts y CLI de Automatización

El directorio `scripts/` y el paquete `src/cli/` contienen herramientas para mantenimiento y tareas programadas:

```powershell
# Barrido desatendido con mínimo 20% de descuento y exportación JSON
python scripts/test_busqueda_max_ofertas.py --min 20 --marcas-calidad

# Exploración de nodos, índices y keywords en vivo de Amazon Creators API
python scripts/explore_search_nodes.py

# Sincronización del catálogo de categorías desde el canal de Telegram
python -m src.cli.sync_categories
```

---

## 📁 Estructura del Proyecto

```
Amazon-Api-Apps/
├── .github/
│   └── workflows/
│       └── ci.yml                 # Integración Continua (GitHub Actions)
├── assets/
│   ├── logo.ico                   # Icono para Windows
│   └── logo.png                   # Logotipo oficial
├── data/
│   └── categories.json            # Catálogo estructurado de categorías y hashtags
├── deploy/
│   ├── Dockerfile.nas             # Construcción para servidor NAS
│   ├── docker-compose.yml         # Orquestación de contenedor
│   ├── GUIA_SYNOLOGY.md           # Guía paso a paso para NAS Synology
│   └── requirements_server.txt    # Dependencias mínimas para servidor
├── docs/                          # Documentación técnica exhaustiva
│   ├── ARQUITECTURA.md            # Diagramas y desglose detallado de capas
│   ├── FUNCIONALIDAD.md           # Especificación funcional de cada módulo
│   ├── DESARROLLO.md              # Normas de contribución y estándares
│   ├── buscador_chollos.md        # Documento de diseño del motor de búsqueda
│   └── KeepaImplementacion.md     # Algoritmo y fórmulas de evaluación Keepa
├── scripts/                       # Utilidades de mantenimiento e investigación
│   ├── explore_search_nodes.py    # Auditoría de BrowseNodes en vivo
│   └── test_busqueda_max_ofertas.py # Script de barrido masivo sin GUI
├── src/
│   ├── cli/                       # Puntos de entrada por consola
│   ├── config/                    # Carga y validación de variables de entorno
│   ├── domain/                    # Entidades y lógica pura de negocio
│   ├── formatters/                # Formateadores de texto HTML y Telegram
│   ├── integrations/              # Clientes de APIs externas (Amazon, OpenAI, etc.)
│   ├── server/                    # API REST con FastAPI
│   ├── services/                  # Fachadas de aplicación
│   ├── ui/                        # Vistas de escritorio con Tkinter/ttkbootstrap
│   └── use_cases/                 # Orquestación de casos de uso + puertos
├── tests/
│   ├── unit/                      # Pruebas unitarias de dominio y formateadores
│   └── integration/               # Pruebas de integración de casos de uso
├── .dockerignore                  # Exclusiones de construcción Docker
├── .env.example                   # Plantilla documentada de variables de entorno
├── .gitignore                     # Exclusiones estrictas de Git
├── BuscarChollos.spec             # Especificación PyInstaller para Buscador
├── PublicadorBuenChollo.spec      # Especificación PyInstaller para Publicador
├── LICENSE                        # Licencia MIT
├── requirements.txt               # Dependencias completas del proyecto
├── run_deals_gui.py               # Launcher del Buscador de Chollos
└── run_gui.py                     # Launcher del Publicador BuenChollo
```

---

## 📋 Requisitos Previos

- **Python 3.11, 3.12 o 3.14** instalado.
- Cuenta de **Amazon Associates / Amazon Creators API** con credenciales LWA activas.
- Bot de **Telegram** creado vía [@BotFather](https://t.me/BotFather).
- *(Opcional)* Clave de **OpenAI API** para redacción automática con GPT.
- *(Opcional)* Suscripción y clave de **Keepa API** para filtrado histórico de precios.

---

## 🚀 Instalación y Puesta en Marcha

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/Amazon-Api-Apps.git
cd Amazon-Api-Apps
```

### 2. Crear y Activar Entorno Virtual

**En Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**En Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## ⚙️ Configuración de Entorno (.env)

Copia la plantilla `.env.example` y crea tu archivo `.env` en la raíz del proyecto:

```powershell
Copy-Item .env.example .env    # Windows PowerShell
# o en Linux/macOS:
cp .env.example .env
```

Edita `.env` con tus credenciales. A continuación se detallan las variables admitidas:

| Variable | Requerido | Descripción | Origen / Enlace |
|---|---|---|---|
| `AMAZON_CLIENT_ID` | **Sí** | Client ID de Login with Amazon (LWA) | [Amazon Associates Portal](https://affiliate-program.amazon.es/) |
| `AMAZON_CLIENT_SECRET` | **Sí** | Client Secret LWA | Amazon Developer Console |
| `AMAZON_AFFILIATE_TAG` | **Sí** | Tag de seguimiento de afiliados (ej: `mitag-21`) | Amazon Associates |
| `AMAZON_MARKETPLACE` | No | Marketplace objetivo (defecto: `www.amazon.es`) | Configuración regional |
| `TELEGRAM_BOT_TOKEN` | **Sí** | Token HTTP del bot de Telegram | [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_ADMIN_CHANNEL_ID` | **Sí** | ID del canal/grupo privado para previsualización | Telegram (`-100...`) |
| `TELEGRAM_MAIN_CHANNEL_ID` | No | ID del canal público final de ofertas | Telegram (`-100...`) |
| `OPENAI_API_KEY` | No | Clave de OpenAI para redactar textos con GPT | [OpenAI Platform](https://platform.openai.com/api-keys) |
| `KEEPA_API_KEY` | No | Clave de Keepa para auditar precio medio de 90 días | [Keepa API](https://keepa.com/#!api) |
| `TELEGRAM_USER_API_ID` | No | API ID de Telethon (solo lectura de histórico) | [my.telegram.org](https://my.telegram.org/apps) |
| `TELEGRAM_USER_API_HASH` | No | API Hash de Telethon (solo lectura de histórico) | [my.telegram.org](https://my.telegram.org/apps) |
| `NAS_SERVER_URL` | No | URL del servidor backend (defecto: `http://localhost:8000`) | Servidor local o NAS |

> [!CAUTION]
> **NUNCA** subas tu archivo `.env` a GitHub ni lo compartas. El repositorio incluye un `.gitignore` preconfigurado para proteger tus claves en todo momento.

---

## 🖥️ Guía de Uso Rápido

### Iniciar las Aplicaciones de Escritorio

Ambas GUIs deben ejecutarse desde la raíz del proyecto para que los imports relativos del paquete `src` se resuelvan correctamente:

```powershell
# 1. Buscador interactivo de ofertas:
python run_deals_gui.py

# 2. Generador y publicador a Telegram:
python run_gui.py
```

### Iniciar el Servidor REST (FastAPI)

```powershell
uvicorn src.server.nas_api:app --host 0.0.0.0 --port 8000 --reload
```
Accede a la documentación interactiva Swagger UI en: `http://localhost:8000/docs`.

---

## 📦 Compilación a Ejecutables Windows (.exe)

El proyecto incluye archivos de especificación para **PyInstaller** optimizados para empaquetar ejecutables independientes (standalone) con soporte de assets y sin empaquetar claves privadas:

```powershell
# Compilar Buscador de Chollos -> dist/BuscarChollos/BuscarChollos.exe
pyinstaller BuscarChollos.spec --noconfirm

# Compilar Publicador -> dist/PublicadorBuenChollo/PublicadorBuenChollo.exe
pyinstaller PublicadorBuenChollo.spec --noconfirm
```

*Nota: También puedes usar el script de compilación directa `build_buscar_chollos.bat`.*

---

## 🐳 Despliegue con Docker (NAS / Servidor)

Para desplegar el servicio de fondo en un NAS Synology u otro entorno Docker:

```bash
docker-compose -f deploy/docker-compose.yml up -d --build
```

- **Puerto:** `8000`
- **Zona Horaria:** Configurada en `Europe/Madrid`
- **Guía de Configuración Synology:** Consulta [`deploy/GUIA_SYNOLOGY.md`](deploy/GUIA_SYNOLOGY.md) para configurar el contenedor en Container Manager con reinicio automático.

---

## 🧪 Testing y Calidad de Código

El repositorio cuenta con una suite integral de **99 tests automatizados** que cubren lógica de dominio, parseadores, cálculo de descuentos, métricas de Keepa y orquestación de casos de uso:

```powershell
# Ejecutar toda la suite de pruebas:
pytest

# Ejecución rápida en modo silencioso:
pytest -q

# Ejecutar únicamente pruebas unitarias de dominio:
pytest tests/unit -q

# Ejecutar pruebas de integración:
pytest tests/integration -q
```

### Convenciones de Desarrollo

- **Docstrings descriptivos:** Cada módulo `.py` comienza con una cabecera explicando su propósito y rol arquitectónico.
- **Sin `print` en producción:** Todo evento de diagnóstico se canaliza a través de `logging`.
- **Clean Architecture estricta:** La capa de UI jamás ejecuta lógica de negocio directa.

---

## 🔒 Seguridad y Buenas Prácticas

1. **Aislamiento de Secretos:** `.env`, `.env.*` y las bases de datos de sesión de Telegram (`runtime/*.session`) están rigurosamente excluidos en `.gitignore` y `.dockerignore`.
2. **Rate Limiting:** La integración con Amazon Creators API incluye pausas controladas para respetar el límite estricto de ~1 petición por segundo por par de credenciales LWA.
3. **Caché de Tokens LWA:** El token de autenticación de Amazon se renueva automáticamente antes de expirar y se almacena en memoria evitando peticiones OAuth redundantes.
4. **Respeto a las Políticas de Afiliados:** La aplicación respeta los términos de servicio del programa de afiliados de Amazon y el etiquetado correcto de links.

---

## 📚 Documentación Adicional

- [Arquitectura Detallada (`docs/ARQUITECTURA.md`)](docs/ARQUITECTURA.md) — Diagrama de componentes, puertos y flujo de datos.
- [Especificación Funcional (`docs/FUNCIONALIDAD.md`)](docs/FUNCIONALIDAD.md) — Detalle de interacción de cada botón, panel y vista.
- [Guía de Desarrollo (`docs/DESARROLLO.md`)](docs/DESARROLLO.md) — Entorno de trabajo, directrices de código y testing.
- [Diseño del Buscador de Chollos (`docs/buscador_chollos.md`)](docs/buscador_chollos.md) — Algoritmo de rotación de SortBy y doble barrido.
- [Implementación de Keepa (`docs/KeepaImplementacion.md`)](docs/KeepaImplementacion.md) — Detección algorítmica de rebajas reales vs precios inflados.
- [Guía Synology NAS (`deploy/GUIA_SYNOLOGY.md`)](deploy/GUIA_SYNOLOGY.md) — Despliegue en Synology DSM 7+.

---

## 📄 Licencia

Este proyecto está bajo la Licencia **MIT**. Consulta el archivo [LICENSE](LICENSE) para más detalles.
