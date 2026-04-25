# 🛠️ Guía de Desarrollo e Instrucciones para IAs

## 🎨 Estilo de Código y Convenciones
- **Encabezados:** Cada archivo `.py` debe iniciar con un docstring (`""" ... """`) que explique su función principal para un desarrollador junior.
- **Comentarios:** El código debe ser autodocumentado (nombres claros). Los comentarios se reservan para explicar decisiones de diseño o lógica no evidente.
- **Naming:** `snake_case` para variables/funciones, `PascalCase` para clases.

## 🛠️ Manejo de Errores
1.  **Capa de Integración:** Capturar excepciones específicas de red o API y relanzarlas como excepciones de dominio o devolver `None` con un log de error claro.
2.  **UI:** Siempre envolver las llamadas a casos de uso en bloques `try/except` para mostrar alertas visuales al usuario (usando `messagebox` de tkinter) y evitar que la app se cierre.

## 🧩 Patrones de Diseño Preferidos
- **Dependency Injection:** Los casos de uso reciben sus servicios en el constructor. Esto facilita los tests unitarios.
- **Singleton/Statics:** Para servicios que no mantienen estado complejo (como `AmazonService`), se prefieren métodos estáticos o instancias compartidas.
- **Repository Pattern:** Para el acceso a datos (`JSONCategoryRepository`), ocultando si los datos vienen de un archivo, una base de datos o una API.

## 🧪 Testing y Verificación
- **Obligatoriedad:** Toda funcionalidad nueva o modificada debe incluir tests en la carpeta `tests/`.
- **Cobertura:** Se deben testear los casos de uso (`use_cases`) y los servicios críticos.
- **Herramientas:** Usar `pytest`.

## 🚀 Gestión de Git y Documentación
- **Control Manual:** NO realizar commits ni pushes de forma automática. Se requiere confirmación explícita del usuario.
- **Regla Triple de Doc:** Cada cambio funcional requiere actualizar:
    1. `AGENTS.md`.
    2. Carpeta `docs/`.
    3. Carpeta `context/`.
- **Mantenimiento del Contexto:** Antes de cada commit, sugerir la actualización de los archivos en `context/`.
