"""
Interfaz Gráfica: Buscador de Chollos
Esta ventana permite buscar productos en oferta de Amazon por categoría,
filtrando por rango de descuento y cantidad de resultados. Al seleccionar
un producto de la lista, muestra su imagen principal y su gráfica de precio
histórico de Keepa para ayudar a decidir si el chollo es realmente bueno. Es de solo consulta:
no publica nada en Telegram (para eso está la otra GUI, main_gui.py).
"""

import ctypes
import io
import logging
import os
import sys
import threading
import webbrowser
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox

import requests
import ttkbootstrap as ttk
from PIL import Image, ImageTk

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.use_cases.find_deals import FindDealsUseCase
from src.use_cases.filter_deals_keepa import FilterDealsKeepaUseCase
from src.use_cases.filter_chollos_calidad import FilterChollosCalidadUseCase
from src.domain.categories_search_index import CATEGORY_DISPLAY_NAMES
from src.domain.entities import ProductInfo
from src.domain.marcas_calidad import es_marca_calidad
from src.integrations.storage.deals_json import guardar_ofertas_json, productos_desde_json

logger = logging.getLogger(__name__)

KEEPA_GRAPH_URL = "https://graph.keepa.com/pricehistory.png?asin={asin}&domain=es"
# Keepa bloquea (403 vía Cloudflare) las peticiones sin User-Agent de navegador.
KEEPA_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
# "Max" = sin límite: devuelve todo lo que encuentre (la API de Amazon
# permite como máximo ~100 productos por categoría, 10 páginas de ~10).
OPCIONES_CANTIDAD = ["5", "10", "20", "50", "Max"]
# Opción especial del desplegable que busca en todas las categorías a la vez.
OPCION_TODAS = "Todas las categorías"
# Valores que aparecen seleccionados al abrir el buscador de chollos.
DESCUENTO_MINIMO_PREDETERMINADO = "15"
DESCUENTO_MAXIMO_PREDETERMINADO = "50"
CANTIDAD_PREDETERMINADA = "Max"
# Tras abrir el navegador vigilamos el foco durante unos segundos (13 × 300 ms
# ≈ 4 s) y lo recuperamos si otra ventana se pone delante. El navegador puede
# tardar poco (ya abierto) o varios segundos (arranque en frío), por eso se
# vigila un rato en vez de reintentar en momentos fijos.
VIGILANCIA_FOCO_INTENTOS = 13
VIGILANCIA_FOCO_INTERVALO_MS = 300

# Prefijo de los JSON que exporta el barrido de ofertas (data/max_ofertas_*).
PREFIJO_JSON_BARRIDO = "max_ofertas_"

# Valores por defecto (provisionales) de las métricas del filtro Keepa.
# Se definirán con el usuario cuando se implemente la valoración automática.
KEEPA_AHORRO_VS_MEDIA_DEFECTO = "10"
KEEPA_MARGEN_SOBRE_MINIMO_DEFECTO = "5"
KEEPA_DIAS_HISTORIA_DEFECTO = "90"


class DealsGUI:
    """Ventana principal del buscador de chollos."""

    def __init__(self, root):
        self.root = root
        self.root.title("Buscador de Chollos")
        self.root.geometry("1300x750")
        self.root.minsize(1000, 650)

        self.use_case = FindDealsUseCase()
        self.keepa_use_case = FilterDealsKeepaUseCase()
        self.calidad_use_case = FilterChollosCalidadUseCase()
        self.chollos: list = []
        # Lista "en bruto" del barrido completo, ANTES del filtrado Keepa: es
        # sobre la que se aplica el filtro (puede re-aplicarse con otra config).
        self.chollos_brutos: list = []
        self.producto_seleccionado = None
        # Intentos de vigilancia de foco pendientes (0 = no se está vigilando).
        self._intentos_foco = 0

        self._build_ui()

    def _build_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # --- Panel de filtros ---
        filtros_frame = ttk.LabelFrame(main_frame, text=" Filtros de búsqueda ")
        filtros_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(filtros_frame, text="Categoría:").pack(side=tk.LEFT, padx=(8, 5), pady=8)
        self.combo_categoria = ttk.Combobox(
            filtros_frame,
            values=[OPCION_TODAS] + CATEGORY_DISPLAY_NAMES,
            state="readonly",
            width=25,
        )
        self.combo_categoria.set(OPCION_TODAS)
        self.combo_categoria.pack(side=tk.LEFT, padx=5)

        ttk.Label(filtros_frame, text="Descuento mín. %:").pack(side=tk.LEFT, padx=(15, 5))
        self.entry_min = ttk.Entry(filtros_frame, width=6)
        self.entry_min.insert(0, DESCUENTO_MINIMO_PREDETERMINADO)
        self.entry_min.pack(side=tk.LEFT, padx=5)

        ttk.Label(filtros_frame, text="Descuento máx. %:").pack(side=tk.LEFT, padx=(15, 5))
        self.entry_max = ttk.Entry(filtros_frame, width=6)
        self.entry_max.insert(0, DESCUENTO_MAXIMO_PREDETERMINADO)
        self.entry_max.pack(side=tk.LEFT, padx=5)

        ttk.Label(filtros_frame, text="Nº chollos:").pack(side=tk.LEFT, padx=(15, 5))
        self.combo_cantidad = ttk.Combobox(filtros_frame, values=OPCIONES_CANTIDAD, state="readonly", width=6)
        self.combo_cantidad.set(CANTIDAD_PREDETERMINADA)
        self.combo_cantidad.pack(side=tk.LEFT, padx=5)

        self.btn_buscar = ttk.Button(filtros_frame, text="🔍 Buscar chollos", command=self.start_search, bootstyle="primary")
        self.btn_buscar.pack(side=tk.LEFT, padx=15, pady=8)

        self.btn_buscar_todos = ttk.Button(
            filtros_frame,
            text="⚡ Buscar TODOS los chollos",
            command=self.start_buscar_todos,
            bootstyle="success",
        )
        self.btn_buscar_todos.pack(side=tk.LEFT, padx=(0, 15), pady=8)

        self.btn_cargar = ttk.Button(
            filtros_frame,
            text="📂 Cargar resultados",
            command=self.cargar_resultados_json,
            bootstyle="secondary",
        )
        self.btn_cargar.pack(side=tk.LEFT, padx=(0, 15), pady=8)

        # --- Panel de filtrado Keepa ---
        keepa_frame = ttk.LabelFrame(main_frame, text=" Filtrado por Keepa (valoración automática) ")
        keepa_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(keepa_frame, text="Ahorro vs media %:").pack(side=tk.LEFT, padx=(8, 5), pady=8)
        self.entry_ahorro_media = ttk.Entry(keepa_frame, width=6)
        self.entry_ahorro_media.insert(0, KEEPA_AHORRO_VS_MEDIA_DEFECTO)
        self.entry_ahorro_media.pack(side=tk.LEFT, padx=5)

        ttk.Label(keepa_frame, text="Margen sobre mínimo %:").pack(side=tk.LEFT, padx=(15, 5))
        self.entry_margen_minimo = ttk.Entry(keepa_frame, width=6)
        self.entry_margen_minimo.insert(0, KEEPA_MARGEN_SOBRE_MINIMO_DEFECTO)
        self.entry_margen_minimo.pack(side=tk.LEFT, padx=5)

        ttk.Label(keepa_frame, text="Días de historia mín.:").pack(side=tk.LEFT, padx=(15, 5))
        self.entry_dias_historia = ttk.Entry(keepa_frame, width=6)
        self.entry_dias_historia.insert(0, KEEPA_DIAS_HISTORIA_DEFECTO)
        self.entry_dias_historia.pack(side=tk.LEFT, padx=5)

        self.btn_filtrar_keepa = ttk.Button(
            keepa_frame,
            text="🎯 Filtrar por Keepa",
            command=self.filtrar_por_keepa,
            bootstyle="warning",
        )
        self.btn_filtrar_keepa.pack(side=tk.LEFT, padx=15, pady=8)

        self.btn_buscar_filtrar = ttk.Button(
            keepa_frame,
            text="🚀 Buscar TODOS y filtrar",
            command=self.buscar_y_filtrar,
            bootstyle="danger",
        )
        self.btn_buscar_filtrar.pack(side=tk.LEFT, padx=(0, 15), pady=8)

        # --- Panel de filtrado de calidad (marcas) ---
        calidad_frame = ttk.LabelFrame(main_frame, text=" ⭐ Filtro de calidad (marcas fiables) ")
        calidad_frame.pack(fill=tk.X, pady=(0, 10))

        self.var_solo_marcas = tk.BooleanVar(value=True)
        self.chk_solo_marcas = ttk.Checkbutton(
            calidad_frame,
            text="Solo marcas de calidad",
            variable=self.var_solo_marcas,
        )
        self.chk_solo_marcas.pack(side=tk.LEFT, padx=(8, 15), pady=8)

        self.btn_filtrar_calidad = ttk.Button(
            calidad_frame,
            text="⭐ Filtrar por calidad",
            command=self.filtrar_por_calidad,
            bootstyle="info",
        )
        self.btn_filtrar_calidad.pack(side=tk.LEFT, padx=15, pady=8)

        self.btn_buscar_filtrar_calidad = ttk.Button(
            calidad_frame,
            text="🚀 Buscar TODOS y filtrar calidad",
            command=self.buscar_y_filtrar_calidad,
            bootstyle="success",
        )
        self.btn_buscar_filtrar_calidad.pack(side=tk.LEFT, padx=(0, 15), pady=8)

        # --- Botón de ordenación por fecha de caducidad ---
        self.orden_fecha = None  # None=desordenado, "asc", "desc"
        self.btn_orden_fecha = ttk.Button(
            calidad_frame,
            text="📅 Caducidad (sin orden)",
            command=self.alternar_orden_fecha,
            bootstyle="secondary",
        )
        self.btn_orden_fecha.pack(side=tk.LEFT, padx=(0, 15), pady=8)

        # --- Panel de resultados (izquierda) + detalle (derecha) ---
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        resultados_frame = ttk.LabelFrame(content_frame, text=" Resultados ")
        resultados_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        columnas = ("marca", "descuento", "titulo", "precio")
        self.tree = ttk.Treeview(resultados_frame, columns=columnas, show="headings", bootstyle="primary")
        self.tree.heading("marca", text="Marca")
        self.tree.heading("descuento", text="Dto.")
        self.tree.heading("titulo", text="Producto")
        self.tree.heading("precio", text="Precio")
        self.tree.column("marca", width=110)
        self.tree.column("descuento", width=60, anchor="center")
        self.tree.column("titulo", width=290)
        self.tree.column("precio", width=90, anchor="e")
        self.tree.tag_configure("calidad", foreground="#2e7d32")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll_y = ttk.Scrollbar(resultados_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.on_select_producto)
        # Enter sobre la lista abre el producto seleccionado en Amazon, para
        # poder recorrer los chollos con las flechas sin soltar el teclado.
        self.tree.bind("<Return>", lambda event: self.abrir_en_amazon())

        # --- Panel de detalle ---
        detalle_frame = ttk.LabelFrame(content_frame, text=" Detalle y gráfica Keepa ", width=480)
        detalle_frame.pack(side=tk.RIGHT, fill=tk.Y)
        detalle_frame.pack_propagate(False)

        self.lbl_titulo = ttk.Label(detalle_frame, text="Selecciona un producto de la lista", wraplength=440, font=("Segoe UI", 11, "bold"))
        self.lbl_titulo.pack(anchor="w", padx=10, pady=(10, 5))

        self.lbl_precio = ttk.Label(detalle_frame, text="", font=("Segoe UI", 10))
        self.lbl_precio.pack(anchor="w", padx=10)

        self.lbl_link = ttk.Label(detalle_frame, text="", wraplength=440, font=("Segoe UI", 8), bootstyle="secondary")
        self.lbl_link.pack(anchor="w", padx=10, pady=(0, 5))

        self.btn_abrir_amazon = ttk.Button(
            detalle_frame, text="🛒 Abrir en Amazon", command=self.abrir_en_amazon, bootstyle="outline-warning"
        )
        self.btn_abrir_amazon.pack(anchor="w", padx=10, pady=(0, 10))

        # Imagen principal del producto (encima de la gráfica Keepa).
        self.imagen_label = ttk.Label(detalle_frame, text="")
        self.imagen_label.pack(padx=10, pady=(0, 5))

        self.keepa_label = ttk.Label(detalle_frame, text="")
        self.keepa_label.pack(padx=10, pady=(5, 5), expand=True)

        self.lbl_caducidad = ttk.Label(detalle_frame, text="", font=("Segoe UI", 12, "bold"), bootstyle="danger")
        self.lbl_caducidad.pack(anchor="center", padx=10, pady=(5, 10))

        # --- Barra de estado ---
        self.status_var = tk.StringVar()
        self.status_var.set("  Esperando búsqueda...")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w", padding=2)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _set_busy(self, busy: bool):
        """Deshabilita/habilita los botones de acción durante una operación larga."""
        estado = ['disabled'] if busy else ['!disabled']
        for boton in (self.btn_buscar, self.btn_buscar_todos, self.btn_cargar,
                      self.btn_filtrar_keepa, self.btn_buscar_filtrar,
                      self.btn_filtrar_calidad, self.btn_buscar_filtrar_calidad,
                      self.btn_orden_fecha):
            boton.state(estado)
        self.root.update_idletasks()

    def start_search(self):
        categoria = self.combo_categoria.get()
        rango = self._rango_descuento_desde_entries()
        if rango is None:
            return
        min_descuento, max_descuento = rango

        cantidad_texto = self.combo_cantidad.get()
        # None = sin límite: el caso de uso devuelve todo lo que encuentre.
        limite = None if cantidad_texto == "Max" else int(cantidad_texto)

        self._set_busy(True)
        self.status_var.set(f"  Buscando chollos en '{categoria}'...")
        self.tree.delete(*self.tree.get_children())
        self.chollos = []

        thread = threading.Thread(
            target=self._run_search,
            args=(categoria, min_descuento, max_descuento, limite),
        )
        thread.daemon = True
        thread.start()

    def _rango_descuento_desde_entries(self):
        """Lee y valida los campos de descuento mín/máx. Devuelve (min, max) o
        None si algún valor no es un número (mostrando un aviso)."""
        try:
            min_descuento = int(self.entry_min.get() or 0)
        except ValueError:
            messagebox.showwarning("Aviso", "El descuento mínimo debe ser un número.")
            return None

        max_texto = self.entry_max.get().strip()
        max_descuento = None
        if max_texto:
            try:
                max_descuento = int(max_texto)
            except ValueError:
                messagebox.showwarning("Aviso", "El descuento máximo debe ser un número.")
                return None
        return min_descuento, max_descuento

    def _run_search(self, categoria, min_descuento, max_descuento, limite):
        try:
            if categoria == OPCION_TODAS:
                chollos = self.use_case.execute_todas(
                    CATEGORY_DISPLAY_NAMES,
                    min_descuento=min_descuento,
                    max_descuento=max_descuento,
                    limite=limite,
                    on_progress=self._avisar_progreso_mensaje,
                )
            else:
                chollos = self.use_case.execute(
                    categoria,
                    min_descuento=min_descuento,
                    max_descuento=max_descuento,
                    limite=limite,
                )
            self.root.after(0, self._show_results, chollos)
        except ValueError as e:
            self.root.after(0, self._show_error, str(e))
        except Exception as e:
            self.root.after(0, self._show_error, f"Error inesperado: {e}")

    def _avisar_progreso_mensaje(self, mensaje):
        """Actualiza la barra de estado con el progreso de la búsqueda. Se
        llama desde el hilo de búsqueda, por eso usamos root.after (los
        widgets de Tkinter solo pueden tocarse desde el hilo principal)."""
        self.root.after(0, self.status_var.set, f"  {mensaje}")

    def _show_results(self, chollos):
        self._set_busy(False)
        self.chollos = chollos

        if not chollos:
            self.status_var.set("  No se encontraron chollos con esos filtros.")
            return

        self._poblar_tree(chollos)
        self.status_var.set(f"  {len(chollos)} chollos encontrados.")

    def _poblar_tree(self, chollos):
        """Llena la tabla de resultados con la lista de productos dada.

        Las marcas de calidad se marcan con ★ y en color verde para poder
        escanear el listado de un vistazo, además del orden con prioridad
        de marca que ya aplica el caso de uso."""
        self.tree.delete(*self.tree.get_children())
        for i, p in enumerate(chollos):
            precio = f"{p.precio_actual:.2f} {p.moneda}" if p.precio_actual else "-"
            calidad = es_marca_calidad(p.marca)
            marca = f"★ {p.marca}" if (calidad and p.marca) else (p.marca or "-")
            tags = ("calidad",) if calidad else ()
            self.tree.insert(
                "", tk.END, iid=str(i),
                values=(marca, f"-{p.descuento_porcentaje}%", p.titulo, precio),
                tags=tags,
            )

    # ── Barrido completo de todas las categorías tech ────────────────────
    def start_buscar_todos(self, filtrar_despues: bool = False, filtrar_calidad_despues: bool = False):
        """Lanza la búsqueda de TODOS los chollos en las categorías tech.

        Es el equivalente desde la GUI a scripts/test_busqueda_max_ofertas.py:
        recorre las 24 categorías tech con SortBy + barrido por marcas y guarda el
        JSON con todas las ofertas. Si filtrar_despues es True, al terminar se
        aplica automáticamente el filtro Keepa configurado; si
        filtrar_calidad_despues es True, el filtro de calidad (marcas).
        """
        rango = self._rango_descuento_desde_entries()
        if rango is None:
            return
        min_descuento, max_descuento = rango

        self._set_busy(True)
        self.status_var.set("  Buscando TODOS los chollos en las categorías tech... (puede tardar 15-40 min)")
        self.tree.delete(*self.tree.get_children())
        self.chollos = []
        self.chollos_brutos = []

        thread = threading.Thread(
            target=self._run_buscar_todos,
            args=(min_descuento, max_descuento, filtrar_despues, filtrar_calidad_despues),
        )
        thread.daemon = True
        thread.start()

    def _run_buscar_todos(self, min_descuento, max_descuento, filtrar_despues, filtrar_calidad_despues):
        try:
            chollos = self.use_case.execute_todas(
                CATEGORY_DISPLAY_NAMES,
                min_descuento=min_descuento,
                max_descuento=max_descuento,
                limite=None,  # Sin tope: se devuelven todos los chollos.
                on_progress=self._avisar_progreso_mensaje,
                incluir_marcas=True,
            )
            ruta = None
            try:
                ruta = guardar_ofertas_json(
                    chollos,
                    self._path_barrido_actual(),
                    metadatos={
                        "min_descuento": min_descuento,
                        "max_descuento": max_descuento,
                        "incluir_marcas": True,
                    },
                )
            except Exception as e:
                # El guardado es secundario: si falla, seguimos mostrando los
                # resultados (el usuario puede exportarlos con 📂 Cargar).
                logger.warning("No se pudo guardar el JSON del barrido: %s", e)
            self.root.after(
                0, self._mostrar_barrido,
                chollos, ruta, filtrar_despues, filtrar_calidad_despues,
            )
        except ValueError as e:
            self.root.after(0, self._show_error, str(e))
        except Exception as e:
            self.root.after(0, self._show_error, f"Error inesperado: {e}")

    def _mostrar_barrido(self, chollos, ruta, filtrar_despues, filtrar_calidad_despues):
        self._set_busy(False)
        self.chollos_brutos = list(chollos)
        self.chollos = list(chollos)

        if not chollos:
            self.status_var.set("  No se encontraron chollos en el barrido.")
            return

        self._poblar_tree(chollos)
        guardado = f" · guardado en {os.path.basename(ruta)}" if ruta else ""
        self.status_var.set(f"  {len(chollos)} chollos encontrados en todas las categorías{guardado}.")

        if filtrar_despues:
            self.filtrar_por_keepa()
        if filtrar_calidad_despues:
            self.filtrar_por_calidad()

    def _path_barrido_actual(self):
        """Ruta del JSON donde se guarda el barrido actual (data/max_ofertas_*)."""
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'data'))
        nombre = f"{PREFIJO_JSON_BARRIDO}{datetime.now():%Y%m%d_%H%M%S}.json"
        return os.path.join(data_dir, nombre)

    # ── Filtrado por Keepa ───────────────────────────────────────────────
    def buscar_y_filtrar(self):
        """Acción de un solo clic: barrido completo + filtrado Keepa al final."""
        self.start_buscar_todos(filtrar_despues=True)

    def _config_keepa(self):
        """Lee los umbrales del filtro Keepa de los campos de la GUI."""
        try:
            return {
                "ahorro_vs_media": int(self.entry_ahorro_media.get() or 0),
                "margen_sobre_minimo": int(self.entry_margen_minimo.get() or 0),
                "dias_historia": int(self.entry_dias_historia.get() or 0),
            }
        except ValueError:
            messagebox.showwarning("Aviso", "Las métricas del filtro Keepa deben ser números.")
            return None

    def filtrar_por_keepa(self):
        """Aplica el filtro Keepa a los chollos en bruto y muestra el resultado.

        El filtrado se ejecuta en un hilo (para cuando sí haga llamadas a la
        API de Keepa no congelar la interfaz) y sustituye la tabla actual.
        """
        if not self.chollos_brutos:
            messagebox.showinfo(
                "Aviso",
                "Primero busca los chollos (⚡ Buscar TODOS) o cárgalos (📂 Cargar resultados).",
            )
            return
        config = self._config_keepa()
        if config is None:
            return

        self._set_busy(True)
        self.status_var.set("  Valorando chollos con métricas de Keepa...")
        thread = threading.Thread(target=self._run_filtrar_keepa, args=(config,))
        thread.daemon = True
        thread.start()

    def _run_filtrar_keepa(self, config):
        try:
            filtrados = self.keepa_use_case.execute(self.chollos_brutos, config)
            self.root.after(0, self._mostrar_filtrados, filtrados)
        except Exception as e:
            self.root.after(0, self._show_error, f"Error al filtrar por Keepa: {e}")

    def _mostrar_filtrados(self, filtrados):
        self._set_busy(False)
        self.chollos = list(filtrados)
        self._poblar_tree(self.chollos)
        total = len(self.chollos_brutos)
        self.status_var.set(f"  {len(self.chollos)} de {total} chollos superan el filtro Keepa.")

    # ── Filtrado por calidad (marcas) ───────────────────────────────────
    def buscar_y_filtrar_calidad(self):
        """Acción de un solo clic: barrido completo + filtro de calidad al final."""
        self.start_buscar_todos(filtrar_calidad_despues=True)

    def _config_calidad(self):
        """Lee la configuración del filtro de calidad de los campos de la GUI."""
        return {"solo_marcas_calidad": bool(self.var_solo_marcas.get())}

    def filtrar_por_calidad(self):
        """Aplica el filtro de calidad a los chollos en bruto y muestra el resultado.

        Se ejecuta en un hilo (para no congelar la interfaz con listas grandes)
        y sustituye la tabla actual. La lista completa sigue en chollos_brutos
        por si se quiere re-filtrar o volver a mostrar todo.
        """
        if not self.chollos_brutos:
            messagebox.showinfo(
                "Aviso",
                "Primero busca los chollos (⚡ Buscar TODOS) o cárgalos (📂 Cargar resultados).",
            )
            return
        config = self._config_calidad()

        self._set_busy(True)
        self.status_var.set("  Filtrando por calidad (marcas fiables)...")
        thread = threading.Thread(target=self._run_filtrar_calidad, args=(config,))
        thread.daemon = True
        thread.start()

    def _run_filtrar_calidad(self, config):
        try:
            filtrados = self.calidad_use_case.execute(self.chollos_brutos, config)
            self.root.after(0, self._mostrar_calidad, filtrados)
        except Exception as e:
            self.root.after(0, self._show_error, f"Error al filtrar por calidad: {e}")

    def _mostrar_calidad(self, filtrados):
        self._set_busy(False)
        self.chollos = list(filtrados)
        self._poblar_tree(self.chollos)
        total = len(self.chollos_brutos)
        self.status_var.set(f"  {len(self.chollos)} de {total} chollos son de marcas de calidad.")

    def alternar_orden_fecha(self):
        """Cicla el orden de caducidad: None → asc → desc → None."""
        if self.orden_fecha is None:
            self.orden_fecha = "asc"
            self.btn_orden_fecha.config(text="📅 Caducidad ↑ (más pronto)")
        elif self.orden_fecha == "asc":
            self.orden_fecha = "desc"
            self.btn_orden_fecha.config(text="📅 Caducidad ↓ (más tarde)")
        else:
            self.orden_fecha = None
            self.btn_orden_fecha.config(text="📅 Caducidad (sin orden)")
            self._poblar_tree(self.chollos)
            self.status_var.set("  Orden original restaurado.")
            return

        self.ordenar_por_caducidad(reverse=(self.orden_fecha == "desc"))

    def ordenar_por_caducidad(self, reverse: bool = False):
        """Ordena los chollos por fecha de caducidad. Los sin fecha al final."""
        def clave_caducidad(p):
            if not p.fin_oferta:
                return (1, datetime.max)
            try:
                fecha = datetime.fromisoformat(p.fin_oferta.replace('Z', ''))
                return (0, fecha)
            except ValueError:
                return (1, datetime.max)

        self.chollos.sort(key=clave_caducidad, reverse=reverse)
        self._poblar_tree(self.chollos)
        orden = "descendente" if reverse else "ascendente"
        self.status_var.set(f"  Ordenado por caducidad ({orden}).")

    def cargar_resultados_json(self):
        """Carga en la tabla un JSON de ofertas del barrido y lo muestra tal cual.

        Así se pueden revisar los resultados acumulados por
        scripts/test_busqueda_max_ofertas.py sin volver a buscar en Amazon,
        con el mismo panel de detalle y la gráfica de Keepa al seleccionar.
        """
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'data'))
        ultimo = self._ultimo_json_ofertas(data_dir)
        path = filedialog.askopenfilename(
            title="Cargar resultados del barrido",
            initialdir=data_dir,
            initialfile=ultimo or "",
            filetypes=[
                ("Resultados del barrido", f"{PREFIJO_JSON_BARRIDO}*.json"),
                ("Todos los JSON", "*.json"),
            ],
        )
        if not path:
            return

        try:
            chollos = productos_desde_json(path)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el archivo:\n{e}")
            return

        if not chollos:
            messagebox.showinfo("Aviso", "El archivo no contiene ofertas.")
            return

        self._set_busy(False)
        self.producto_seleccionado = None
        self.chollos_brutos = list(chollos)
        self.chollos = list(chollos)
        self._poblar_tree(chollos)
        self.status_var.set(f"  Cargados {len(chollos)} chollos desde {os.path.basename(path)}")

    def _ultimo_json_ofertas(self, data_dir: str):
        """Devuelve el nombre del JSON de barrido más reciente en data/, o None."""
        try:
            disponibles = sorted(
                f for f in os.listdir(data_dir)
                if f.startswith(PREFIJO_JSON_BARRIDO) and f.endswith(".json")
            )
        except OSError:
            return None
        return disponibles[-1] if disponibles else None

    def _show_error(self, mensaje: str):
        self._set_busy(False)
        self.status_var.set("  Error en la búsqueda.")
        messagebox.showerror("Error", mensaje)

    def abrir_en_amazon(self):
        """Abre en el navegador la página del producto seleccionado, y devuelve
        el foco a la lista para poder seguir recorriendo chollos con el teclado
        sin tener que volver a la ventana con el ratón."""
        if not self.producto_seleccionado or not self.producto_seleccionado.url_afiliado:
            messagebox.showwarning("Aviso", "Selecciona antes un producto de la lista.")
            return
        webbrowser.open(self.producto_seleccionado.url_afiliado)
        # El navegador se pone delante al abrir la pestaña y no hay forma de
        # evitarlo, así que durante unos segundos vigilamos el foco y lo
        # recuperamos en cuanto lo perdamos.
        ya_vigilando = self._intentos_foco > 0
        self._intentos_foco = VIGILANCIA_FOCO_INTENTOS
        if not ya_vigilando:
            self.root.after(VIGILANCIA_FOCO_INTERVALO_MS, self._vigilar_foco)

    def _vigilar_foco(self):
        """Comprueba periódicamente si otra ventana nos ha quitado el foco y,
        si es así, lo recupera. Se autoprograma hasta agotar los intentos."""
        if self._intentos_foco <= 0:
            return
        self._intentos_foco -= 1
        self._recuperar_foco_si_perdido()
        if self._intentos_foco > 0:
            self.root.after(VIGILANCIA_FOCO_INTERVALO_MS, self._vigilar_foco)

    def _recuperar_foco_si_perdido(self):
        """Trae la ventana de la app de vuelta al frente si no lo está (Windows)."""
        try:
            # El HWND de la ventana real es el padre del widget raíz de Tk.
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            if ctypes.windll.user32.GetForegroundWindow() == hwnd:
                return  # Ya estamos delante, no hay nada que recuperar.
            # Windows solo permite a una app ponerse delante si hay una tecla
            # pulsada en ese momento; simulamos un toque de ALT para cumplirlo.
            ALT = 0x12
            KEYEVENTF_KEYUP = 0x0002
            ctypes.windll.user32.keybd_event(ALT, 0, 0, 0)
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            ctypes.windll.user32.keybd_event(ALT, 0, KEYEVENTF_KEYUP, 0)
        except Exception:
            # Plan B (ej. fuera de Windows): parpadeo de "siempre visible".
            self.root.attributes("-topmost", True)
            self.root.attributes("-topmost", False)
        self.root.focus_force()
        # Devolvemos el foco de teclado a la lista, con la selección intacta,
        # para que las flechas sigan funcionando al instante.
        self.tree.focus_set()

    def on_select_producto(self, event):
        seleccion = self.tree.selection()
        if not seleccion:
            return

        producto = self.chollos[int(seleccion[0])]
        self.producto_seleccionado = producto

        self.lbl_titulo.config(text=producto.titulo)
        precio = f"{producto.precio_actual:.2f} {producto.moneda}" if producto.precio_actual else "Precio no disponible"
        if producto.precio_anterior:
            precio += f"  (antes {producto.precio_anterior:.2f} {producto.moneda}, -{producto.descuento_porcentaje}%)"
        self.lbl_precio.config(text=precio)
        self.lbl_link.config(text=producto.url_afiliado)

        caducidad_text = ""
        if producto.fin_oferta:
            # Formato esperado de API: 2026-08-25T21:59:59Z
            try:
                dt = datetime.strptime(producto.fin_oferta.split('T')[0], "%Y-%m-%d")
                caducidad_text = f"⏳ Caduca: {dt.strftime('%d/%m/%Y')}"
            except Exception:
                caducidad_text = f"⏳ Caduca: {producto.fin_oferta}"
        self.lbl_caducidad.config(text=caducidad_text)

        self.imagen_label.config(image='', text="Cargando imagen...")
        self.keepa_label.config(image='', text="Cargando gráfica Keepa...")

        # Cada descarga va en su propio hilo para que la imagen del producto
        # (rápida) no tenga que esperar a la gráfica de Keepa (más lenta).
        for target in (self._load_imagen_producto, self._load_keepa_graph):
            thread = threading.Thread(target=target, args=(producto,))
            thread.daemon = True
            thread.start()

    def _load_imagen_producto(self, producto):
        try:
            response = requests.get(producto.imagen_principal, timeout=15)
            response.raise_for_status()

            img = Image.open(io.BytesIO(response.content))
            img.thumbnail((220, 170))
            photo = ImageTk.PhotoImage(img)

            self.root.after(0, self._set_label_image, self.imagen_label, photo, producto.asin)
        except Exception:
            self.root.after(0, self._set_label_error, self.imagen_label, "No se pudo cargar la imagen", producto.asin)

    def _load_keepa_graph(self, producto):
        try:
            url = KEEPA_GRAPH_URL.format(asin=producto.asin)
            response = requests.get(url, headers=KEEPA_HEADERS, timeout=15)
            response.raise_for_status()

            img = Image.open(io.BytesIO(response.content))
            img.thumbnail((440, 300))
            photo = ImageTk.PhotoImage(img)

            self.root.after(0, self._set_label_image, self.keepa_label, photo, producto.asin)
        except Exception:
            self.root.after(0, self._set_label_error, self.keepa_label, "No se pudo cargar la gráfica Keepa", producto.asin)

    def _es_seleccion_actual(self, asin: str) -> bool:
        """Comprueba que el producto sigue siendo el seleccionado. Evita que
        una descarga lenta de un producto anterior pise la imagen del actual
        cuando el usuario cambia rápido de selección."""
        return self.producto_seleccionado is not None and self.producto_seleccionado.asin == asin

    def _set_label_image(self, label, photo, asin: str):
        if not self._es_seleccion_actual(asin):
            return
        label.config(image=photo, text="")
        # Guardamos la referencia para que el recolector de basura no la borre.
        label.image = photo

    def _set_label_error(self, label, mensaje: str, asin: str):
        if not self._es_seleccion_actual(asin):
            return
        label.config(image='', text=mensaje)


def main():
    root = ttk.Window(themename="darkly")
    DealsGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
