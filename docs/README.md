# 🚀 Publicador BuenChollo - Automatización Amazon a Telegram

Este proyecto permite extraer ofertas de Amazon, enriquecerlas con Inteligencia Artificial (GPT) y publicarlas directamente en un canal o grupo de Telegram con un formato visual premium y personalizado.

---

## 📍 ¿Dónde está el programa para usarlo?

Para ejecutar el publicador sin abrir código ni terminales:

1.  Ve a la carpeta **`dist`** en la raíz del proyecto.
2.  Entra en la subcarpeta **`PublicadorBuenChollo`**.
3.  Busca el archivo **`PublicadorBuenChollo.exe`** (Verás que lleva el logotipo circular de **BC TECH**).
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

### 4. Interfaz Moderna (Darkly)
- **Tema Oscuro:** Diseño elegante con colores de acción (Verde para publicar, Azul para generar).
- **Logotipo Integrado:** Cabecera profesional con el logo de BC TECH.
- **NAS Oculto:** Opciones de programación avanzada plegables para una vista más limpia.

### 5. Integración con Telegram
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

## 🧪 Calidad y Testing
Siguiendo los principios de Ingeniería de Software, el proyecto incluye una suite de pruebas automatizadas:
- **Ejecutar tests:** `pytest` (desde la raíz usando el entorno virtual).
- **Estructura:**
  - `tests/unit`: Pruebas de lógica pura (formateadores, normalización).
  - `tests/integration`: Pruebas de flujo de casos de uso y repositorios.

**Mandato de Desarrollo:** Toda funcionalidad nueva debe ir acompañada de su test. No se considera terminada una tarea sin validación.

---

¡Disfruta automatizando tus chollos! 🚀_
