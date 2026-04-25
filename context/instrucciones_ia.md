# 🛠️ Guía de Desarrollo e Instrucciones para IAs

## 🎨 Estilo de Código y Convenciones
- **Naming:** `snake_case` para variables y funciones, `PascalCase` para clases.
- **Docstrings:** Usar Google Style o descriptivos cortos en español para explicar el "qué" y el "por qué".
- **Logging:** Usar el módulo `logging` de Python. Evitar `print()` en producción, especialmente en la capa de servicios y servidor.

## 🛠️ Manejo de Errores
1.  **Capa de Integración:** Capturar excepciones específicas de red o API y relanzarlas como excepciones de dominio o devolver `None` con un log de error claro.
2.  **UI:** Siempre envolver las llamadas a casos de uso en bloques `try/except` para mostrar alertas visuales al usuario (usando `messagebox` de tkinter) y evitar que la app se cierre.

## 🧩 Patrones de Diseño Preferidos
- **Dependency Injection:** Los casos de uso reciben sus servicios en el constructor. Esto facilita los tests unitarios.
- **Singleton/Statics:** Para servicios que no mantienen estado complejo (como `AmazonService`), se prefieren métodos estáticos o instancias compartidas.
- **Repository Pattern:** Para el acceso a datos (`JSONCategoryRepository`), ocultando si los datos vienen de un archivo, una base de datos o una API.

## 🧪 Testing y Verificación
- Los tests deben residir en la carpeta `tests/`.
- Antes de modificar `amazon_api.py`, verificar que no se rompa la compatibilidad con el esquema de respuesta de la API v3.2.
- Al modificar el `telegram_formatter.py`, probar con diferentes combinaciones de precios (oferta flash, precio mínimo histórico, sin descuento).

## 🚀 Gestión de Git y Commits
- **Automatización:** El usuario ha otorgado permiso explícito para que, cada vez que se solicite un commit, se realice automáticamente el `git push` a la rama correspondiente.
- **Mensajes:** Mantener la coherencia y claridad en los mensajes de commit.
- **Mantenimiento del Contexto:** Antes de cada commit, sugerir la actualización de los archivos en `context/`.
