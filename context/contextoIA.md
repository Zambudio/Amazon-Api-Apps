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
