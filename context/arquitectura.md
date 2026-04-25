# 🏗️ Arquitectura y Flujo Técnico

Este documento detalla cómo interactúan los componentes del sistema para procesar un "Chollo".

## 🔄 Flujo de Generación de un Post
1.  **Entrada:** Se recibe una URL de Amazon o un ASIN.
2.  **Extracción (`AmazonService`):** Se consulta la API oficial para obtener título, precios, descripción larga e imágenes.
3.  **Enriquecimiento (`GPTService`):**
    - Se envía la descripción técnica a GPT para generar un "copy" atractivo y corto.
    - Se pasan las categorías existentes para que GPT elija las más adecuadas.
4.  **Formateo (`TelegramFormatter`):** Se construye el string final aplicando:
    - Negritas y estructuras de precios.
    - Mapeo de emojis estándar a `custom_emoji_id` (Premium).
    - Cálculo de porcentajes de descuento.
5.  **Publicación (`PublisherService`):** Se envía la imagen seleccionada y el texto a Telegram usando el Bot API.

## 📂 Estructura Detallada de `src/`
- `src/`: El núcleo de la aplicación.
- `docs/`: Manuales y guías del proyecto.
- `assets/`: Logos y recursos estáticos.
- `deploy/`: Todo lo necesario para el despliegue en Docker/NAS.
- `scripts/`: Scripts auxiliares de procesamiento de datos.

## 💎 Sistema de Emojis Premium
El proyecto utiliza una característica avanzada de Telegram: los **Custom Emojis**.
- Archivo clave: `src/integrations/telegram/emoji_mapper.py`.
- Funcionamiento: Reemplaza caracteres de emoji estándar por tags `<tg-emoji id="...">` que solo funcionan en canales con boost o cuentas premium, pero que dan un aspecto visual superior.

## 🚀 Despliegue y Construcción
- **Windows:** Se usa `PyInstaller` con el archivo `PublicadorBuenChollo.spec`. Este archivo gestiona la inclusión del icono y el bundle de dependencias.
- **Servidor:** Dockerizado mediante `Dockerfile.nas` y `docker-compose.yml`. Optimizado para ejecutarse en entornos como Synology.
