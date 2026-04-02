# 🚀 Publicador BuenChollo - Automatización Amazon a Telegram

Este proyecto permite extraer ofertas de Amazon, enriquecerlas con Inteligencia Artificial (GPT) y publicarlas directamente en un canal o grupo de Telegram con un formato visual premium y personalizado.

---

## 📍 ¿Dónde está el programa para usarlo?

Para ejecutar el publicador sin abrir código ni terminales:

1.  Ve a la carpeta **`dist`** en la raíz del proyecto.
2.  Entra en la subcarpeta **`PublicadorBuenChollo`**.
3.  Busca el archivo **`PublicadorBuenChollo.exe`** (tiene un icono de una pluma azul/gris por defecto).
4.  **Recomendación:** Haz clic derecho sobre él y selecciona `Enviar a... > Escritorio (crear acceso directo)` para tenerlo siempre a mano.

> [!IMPORTANT]
> El archivo `.env` en la carpeta principal contiene tus contraseñas y tokens. No lo borres ni lo compartas. El ejecutable lo necesita para conectar con Amazon, OpenAI y Telegram.

---

## 🛠️ Funcionalidades Implementadas

### 1. Extracción de Datos Inteligente (Amazon)
- **Detección de ASIN:** Soporta URLs largas, cortas (`amzn.to`) y ASINs directos.
- **Cálculo de Ahorro:** Obtiene el precio anterior y calcula automáticamente la diferencia en euros y el porcentaje de descuento real.
- **Ofertas Flash:** Detecta si el producto tiene fecha de expiración y añade un aviso dinámico (ej: `⚠️ Finaliza el 12 de abril`).

### 2. Escritura con IA (ChatGPT)
- **Síntesis de Producto:** Toma las características técnicas de Amazon y las convierte en un texto de venta cercano, atractivo y sintetizado.
- **Formateado:** Limpia automáticamente espacios y tabuladores para que el post quede impecable.

### 3. Sistema de Imágenes Premium
- **Carrusel de Fotos:** Al meter un enlace, puedes navegar por las diferentes imágenes del producto (hasta 7 variantes) para elegir la que mejor quede.
- **Subida de Capturas:** Opción de botón "Subir propia foto" para cuando has hecho una captura de pantalla cuadrada personalizada.
- **Visor en Tiempo Real:** Previsualización de gran tamaño (380px) dentro de la propia aplicación.

### 4. Integración con Telegram
- **Emojis Premium:** Convierte automáticamente emojis estándar en iconos animados Premium de Telegram (usando `custom_emoji_id`).
- **Formato Foto + Texto:** Envía la imagen seleccionada y coloca todo el texto de la oferta como pie de foto (caption).

---

## ⚙️ Configuración (.env)
Si necesitas cambiar de canal o de bot, edita el archivo `.env`:
- `AMAZON_AFFILIATE_TAG`: Tu ID de afiliado de Amazon.
- `OPENAI_API_KEY`: API para que ChatGPT escriba las descripciones.
- `TELEGRAM_BOT_TOKEN`: Token obtenido de @BotFather.
- `TELEGRAM_CHANNEL_ID`: ID del grupo/canal de destino (ej: `-100...`).

---

## 📂 Estructura de Carpetas
- `src/`: Todo el código fuente (integraciones, servicios, interfaz).
- `dist/`: Ubicación del programa ejecutable (.exe).
- `.env`: Configuración secreta y tokens.
- `run_gui.py`: Script para lanzar la interfaz desde Python.

---

## 🛠️ Comandos de Mantenimiento

### Actualizar el Ejecutable (.exe)
Si haces cambios en el código (como el estilo de redacción de la IA o el diseño de la ventana), debes volver a generar el ejecutable lanzando este comando en la terminal:

```bash
pyinstaller --noconfirm --onedir --windowed --add-data "src;src" --add-data ".env;." --name "PublicadorBuenChollo" run_gui.py
```

---

¡Disfruta automatizando tus chollos! 🚀_
