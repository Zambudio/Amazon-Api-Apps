# 🤖 AGENTS.md - Directrices Operativas para IA

Este archivo contiene instrucciones técnicas y mandatos críticos para agentes de IA que trabajen en este repositorio.

## ⚖️ Mandatos Prioritarios (Reglas de Oro)
1.  **Arquitectura Limpia (Clean Architecture):** Respeta estrictamente la separación de capas.
2.  **Código Limpio (Clean Code):** Prioriza legibilidad y nombres descriptivos.
3.  **Documentación Junior-Friendly:** Todo archivo `.py` DEBE empezar con un comentario de encabezado que explique de forma sencilla qué hace el archivo. Los comentarios internos deben explicar el "por qué" de la lógica compleja.
4.  **Ingeniería de Software & Testing:** Toda nueva funcionalidad validada DEBE incluir tests en `tests/`.
5.  **Sincronización de Documentación (Regla Triple):** Actualizar siempre `AGENTS.md`, `docs/` y `context/`.

## 🛠️ Comandos de Desarrollo
- **Lanzar GUI:** `python run_gui.py`
- **Lanzar Servidor (NAS):** `uvicorn src.server.nas_api:app --host 0.0.0.0 --port 8000`
- **Pruebas:** Ejecutar `pytest` para validar toda la lógica de negocio.
- **Construcción EXE:** `pyinstaller PublicadorBuenChollo.spec --noconfirm`
- **Docker:** `docker-compose -f deploy/docker-compose.yml up --build`

## 📂 Estructura del Proyecto
- `src/domain/`: Lógica pura, entidades y reglas de negocio.
- `src/use_cases/`: Orquestación de servicios e integraciones.
- `src/services/`: Fachadas de servicios.
- `src/integrations/`: Adaptadores para APIs externas (Amazon, Telegram, OpenAI).
- `src/ui/`: Interfaz gráfica (Tkinter/ttkbootstrap).
- `deploy/`: Configuración de despliegue (Docker, NAS).
- `context/`: Documentación específica para el contexto de la IA.

## 🚀 Flujo de Git y Commits
- **Permiso de Push:** El usuario ha autorizado el `git push` automático tras cada commit solicitado.
- **Sugerencia de Contexto:** Antes de hacer commit, sugiere SIEMPRE actualizar los archivos en la carpeta `context/`.
- **Formato:** Mensajes de commit claros y concisos en español.

## 🐍 Guía de Estilo Python
- Usar **Type Hints** en todas las firmas de funciones.
- Seguir **PEP 8**.
- Docstrings en español explicando el propósito de clases y métodos complejos.
- Evitar el uso de `print()`; usar el módulo `logging`.

## ⚠️ Áreas Críticas
- **Amazon API:** Estamos usando la versión v3.2 (LWA). No modificar la lógica de autenticación en `src/integrations/amazon/` sin validación previa.
- **Seguridad:** Nunca incluyas el archivo `.env` en los commits. Los secretos se gestionan vía `src/config/settings.py`.
