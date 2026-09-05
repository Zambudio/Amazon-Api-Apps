# Guía de usuario — Amazon-Api-Apps

Esta guía explica cómo usar las dos aplicaciones del proyecto sin escribir código.

El proyecto consta de dos programas de escritorio independientes:

| Programa | Qué hace | Ejecutable |
|---|---|---|
| 💻 **Publicador de Ofertas** | Crea y publica chollos en Telegram con IA | `dist/PublicadorBuenChollo/PublicadorBuenChollo.exe` |
| 🎯 **Buscador de Chollos** | Explora ofertas de Amazon sin publicar | `dist/BuscarChollos/BuscarChollos.exe` |

> [!IMPORTANT]
> El archivo `.env` de la carpeta principal contiene tus contraseñas y tokens.
> **No lo borres ni lo compartas.** Los ejecutables lo necesitan para conectar
> con Amazon, OpenAI y Telegram.

---

## 1. Publicador de Ofertas → Telegram

Ventana principal para **crear y publicar** un post de oferta.

### Pasos

1. Abre el **PublicadorBuenChollo.exe** (lleva el logotipo circular de BC TECH).
2. Pega un **enlace de Amazon** (largo o corto `amzn.to`) o un **ASIN** directo en el campo de entrada.
3. El programa extrae automáticamente: título, precio, descuento y oferta flash (si tiene fecha de expiración).
4. Revisa el texto generado por la **IA (ChatGPT)**; puedes elegir entre las **imágenes** del producto (hasta 7) o subir una **captura propia**.
5. Ajusta la **categoría** y los **hashtags**.
6. Pulsa **publicar** y el post (imagen + texto formateado con emojis premium) llega directo al canal/grupo de Telegram configurado.

### Consejos

- El descuento se calcula solo (precio anterior vs actual, en € y %).
- Si el producto tiene oferta flash, el post incluye el aviso dinámico (ej. "⏳ Finaliza el 12 de agosto").

---

## 2. Buscador de Chollos

Ventana de **solo consulta**: sirve para explorar ofertas antes de decidir cuáles publicar.

### Valores iniciales

| Opción | Valor por defecto |
|---|---|
| Categoría | Todas las categorías tech |
| Descuento mínimo | 15 % |
| Descuento máximo | 50 % |
| Número de chollos | Máximo (sin límite) |

### Cómo usarlo

1. Abre el **BuscarChollos.exe**.
2. Elige categoría y rango de descuento (o déjalo en "Todas").
3. Pulsa **Buscar** para una categoría, o **"⚡ Buscar TODOS los chollos"** para el barrido completo (recorre 24 categorías; puede tardar unos minutos).
4. En la tabla, los resultados de **marcas de calidad** aparecen con **★ en verde** para escanear de un vistazo.
5. Pulsa **"📅 Caducidad"** para ordenar por fecha de fin de oferta (ascendente o descendente; los sin fecha van al final).
6. Selecciona un producto: verás al detalle precio, descuento, **fecha de caducidad** y la **gráfica de precio histórico de Keepa**.
7. Pulsa en la URL para **abrir el chollo en Amazon**.

### Extras

- **"⭐ Filtrar por calidad"**: deja solo marcas de calidad, descartando las genéricas poco fiables.
- **"🎯 Filtrar por Keepa"**: valoración automática de si el descuento es real o un señuelo (requiere clave Keepa; si no hay, este botón no filtra).
- **"📂 Cargar resultados"**: reabre un JSON de un barrido anterior (`data/max_ofertas_*.json`) sin volver a buscar.

---

## 3. Calidad y testing

Siguiendo los principios de Ingeniería de Software, el proyecto incluye una suite de pruebas automatizadas:

- **Ejecutar tests:** `pytest` (desde la raíz usando el entorno virtual).
- **Estructura:**
  - `tests/unit`: pruebas de lógica pura (formateadores, normalización, filtros).
  - `tests/integration`: pruebas de flujo de casos de uso y repositorios.

**Mandato de desarrollo:** toda funcionalidad nueva debe ir acompañada de su test. No se considera terminada una tarea sin validación.

---

¡Disfruta automatizando tus chollos! 🚀