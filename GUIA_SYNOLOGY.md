# 🌐 Guía de Despliegue en Synology NAS (Motor de Programación)

Esta guía documenta los pasos necesarios para instalar el componente "Cerebro Servidor" en tu NAS de Synology. Este componente recibirá los comandos de tu programa de Windows y se encargará de guardarlos y publicarlos a la hora programada, de manera autónoma.

---

## 1. Preparación en tu PC (Windows)

Antes de levantar el servidor en el NAS, asegúrate de que el programa de tu PC sabe a quién tiene que hablarle.

1. Abre tu archivo `.env` en tu PC.
2. Añade la variable con la IP de tu NAS (suponiendo que la IP de tu NAS es `192.168.1.50`, pon esto):
   ```env
   NAS_SERVER_URL=http://192.168.1.50:8000
   ```
3. Recuerda copiar este archivo `.env` a la carpeta `/dist/PublicadorBuenChollo/` para que el `PublicadorBuenChollo.exe` se entere del cambio cuando lo compiles.

*(Nota: Solo deberás compilar el .exe una vez desde la terminal con el comando descrito en el `README.md` principal)*

---

## 2. Preparación de los Archivos para el NAS

El servidor en el NAS necesita el código para poder enviar los mensajes por Telegram. 
1. Abre tu **File Station** en Synology DSM.
2. Ve a la carpeta compartida donde guardas tus contenedores (normalmente se llama `/docker` o `/container`).
3. Crea una subcarpeta llamada `API_Amazon_CloudCode`.
4. **Copia todo el código fuente** de este proyecto desde tu ordenador a esa carpeta en el NAS. Importante que estos archivos estén incluidos:
   - Toda la carpeta `src/` (porque ahí está la lógica del bot y `nas_api.py`).
   - El archivo `docker-compose.yml`.
   - El archivo `Dockerfile.nas`.
   - El archivo `requirements_server.txt`.
   - **Crucial:** El archivo `.env`. El NAS necesitará conectarse a internet para enviar, así que debe tener el `TELEGRAM_BOT_TOKEN`, `TELEGRAM_MAIN_CHANNEL_ID` y `TELEGRAM_ADMIN_CHANNEL_ID` habilitados.

---

## 3. Despliegue con Container Manager (Synology)

Dado que Synology incluye la fantástica herramienta Container Manager, usar Docker Compose es casi automático:

1. Abre la aplicación **Container Manager** en tu Synology.
2. En el menú de la izquierda, haz clic en **Proyecto** (Project).
3. Haz clic en **Crear** (Crear un nuevo proyecto).
4. Dale el nombre que quieras (ej: `buenchollo-bot`).
5. En **Ruta** (Path), dale al botón de examinar (`Browse`) y selecciona exactamente la carpeta `API_Amazon_CloudCode` que acabas de subir al NAS mediante File Station. 
6. En **Origen** (Source), selecciona **"Usar un docker-compose.yml existente"** (Use existing docker-compose.yml) — el Container Manager debería detectarlo automáticamente de los archivos de esa carpeta.
7. Opcional: marca la casilla de *"Construir imagen/Build images"* si te lo pide (esto le dirá y usará automáticamente el `Dockerfile.nas`).
8. Clic en **Siguiente** y luego arranca el proyecto.

### ¿Qué ocurrirá durante la instalación?
El NAS empezará a descargar el sistema Linux (`python:3.11-slim`), instalará la librería FastAPI y dejará un puerto abierto (el `8000`). Esto tomará unos minutos. Luego el contenedor se quedará "verde" (En ejecución).

---

## 4. Probando todo junto

1. Una vez Container Manager diga que el contenedor está funcionando, abre tu `PublicadorBuenChollo.exe` en tu PC de Windows.
2. Busca un producto cualquiera y genera el texto.
3. Abajo en los controles, busca **"Programar Publicación (NAS)"**.
4. Selecciona tu "Canal Pruebas Admin".
5. Pon que se publique **a 1 o 2 minutos vista** desde la hora actual.
6. Pulsa en **"☁️ Enviar al NAS para Programar"**.
7. Verás un mensaje de éxito en Windows informándote de que los datos han volado a tu NAS.

Si miras los "Registros" (Logs) del proyecto en el Container Manager de tu Synology, verás un mensaje como:
`🚀 Publicando Post ID 1 programado para...`

Y ¡Magia! A la hora indicada, la notificación saltará en tu móvil desde Telegram.

---

## 🛑 Fallos Comunes
- **Windows da error de conexión o "Timeout" cuando intentas programar:** La IP de tu NAS que pusiste en `NAS_SERVER_URL` es incorrecta, o tienes el corta-fuegos de Windows/Router bloqueando el puerto TCP 8000 en red local.
- **Tu Synology publica sin Iconos animados, pero en Windows sí salían:** Recuerda que (como vimos), los canales deben tener Nivel 4 de Boosts en Telegram para poder disfrutar de los Custom Emojis que el bot les envía. En grupos (como el Admin) saldrán impecables.
- **Falta de librerías al pulsar el botón Windows:** Si falla tras darle a "☁️ Enviar al NAS", acuérdate siempre de que los archivos nuevos creados en Python y librerías importadas como `mimetypes` no estarán en el .exe si no has vuelto a lanzar el `pyinstaller` (usa el comando de la guía del `README.md`).
