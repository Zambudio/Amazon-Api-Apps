"""
Interfaz Gráfica: Buscador de Chollos
Esta ventana permite buscar productos en oferta de Amazon por categoría,
filtrando por rango de descuento y cantidad de resultados. Al seleccionar
un producto de la lista, muestra su gráfica de precio histórico de Keepa
para ayudar a decidir si el chollo es realmente bueno. Es de solo consulta:
no publica nada en Telegram (para eso está la otra GUI, main_gui.py).
"""

import io
import os
import sys
import threading
import webbrowser
import tkinter as tk
from tkinter import messagebox

import requests
import ttkbootstrap as ttk
from PIL import Image, ImageTk

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.use_cases.find_deals import FindDealsUseCase
from src.domain.categories_search_index import CATEGORY_DISPLAY_NAMES

KEEPA_GRAPH_URL = "https://graph.keepa.com/pricehistory.png?asin={asin}&domain=es"
# Keepa bloquea (403 vía Cloudflare) las peticiones sin User-Agent de navegador.
KEEPA_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
OPCIONES_CANTIDAD = ["5", "10", "20", "50", "Max"]
CANTIDAD_MAXIMA = 100


class DealsGUI:
    """Ventana principal del buscador de chollos."""

    def __init__(self, root):
        self.root = root
        self.root.title("Buscador de Chollos")
        self.root.geometry("1300x750")
        self.root.minsize(1000, 650)

        self.use_case = FindDealsUseCase()
        self.chollos: list = []
        self.producto_seleccionado = None

        self._build_ui()

    def _build_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # --- Panel de filtros ---
        filtros_frame = ttk.LabelFrame(main_frame, text=" Filtros de búsqueda ")
        filtros_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(filtros_frame, text="Categoría:").pack(side=tk.LEFT, padx=(8, 5), pady=8)
        self.combo_categoria = ttk.Combobox(filtros_frame, values=CATEGORY_DISPLAY_NAMES, state="readonly", width=25)
        self.combo_categoria.current(0)
        self.combo_categoria.pack(side=tk.LEFT, padx=5)

        ttk.Label(filtros_frame, text="Descuento mín. %:").pack(side=tk.LEFT, padx=(15, 5))
        self.entry_min = ttk.Entry(filtros_frame, width=6)
        self.entry_min.insert(0, "20")
        self.entry_min.pack(side=tk.LEFT, padx=5)

        ttk.Label(filtros_frame, text="Descuento máx. %:").pack(side=tk.LEFT, padx=(15, 5))
        self.entry_max = ttk.Entry(filtros_frame, width=6)
        self.entry_max.pack(side=tk.LEFT, padx=5)

        ttk.Label(filtros_frame, text="Nº chollos:").pack(side=tk.LEFT, padx=(15, 5))
        self.combo_cantidad = ttk.Combobox(filtros_frame, values=OPCIONES_CANTIDAD, state="readonly", width=6)
        self.combo_cantidad.current(1)
        self.combo_cantidad.pack(side=tk.LEFT, padx=5)

        self.btn_buscar = ttk.Button(filtros_frame, text="🔍 Buscar chollos", command=self.start_search, bootstyle="primary")
        self.btn_buscar.pack(side=tk.LEFT, padx=15, pady=8)

        # --- Panel de resultados (izquierda) + detalle (derecha) ---
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        resultados_frame = ttk.LabelFrame(content_frame, text=" Resultados ")
        resultados_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        columnas = ("descuento", "titulo", "precio")
        self.tree = ttk.Treeview(resultados_frame, columns=columnas, show="headings", bootstyle="primary")
        self.tree.heading("descuento", text="Dto.")
        self.tree.heading("titulo", text="Producto")
        self.tree.heading("precio", text="Precio")
        self.tree.column("descuento", width=60, anchor="center")
        self.tree.column("titulo", width=350)
        self.tree.column("precio", width=90, anchor="e")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll_y = ttk.Scrollbar(resultados_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.on_select_producto)

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

        self.keepa_label = ttk.Label(detalle_frame, text="")
        self.keepa_label.pack(padx=10, pady=10, expand=True)

        # --- Barra de estado ---
        self.status_var = tk.StringVar()
        self.status_var.set("  Esperando búsqueda...")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w", padding=2)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _set_busy(self, busy: bool):
        self.btn_buscar.state(['disabled'] if busy else ['!disabled'])
        self.root.update_idletasks()

    def start_search(self):
        categoria = self.combo_categoria.get()

        try:
            min_descuento = int(self.entry_min.get() or 0)
        except ValueError:
            messagebox.showwarning("Aviso", "El descuento mínimo debe ser un número.")
            return

        max_texto = self.entry_max.get().strip()
        max_descuento = None
        if max_texto:
            try:
                max_descuento = int(max_texto)
            except ValueError:
                messagebox.showwarning("Aviso", "El descuento máximo debe ser un número.")
                return

        cantidad_texto = self.combo_cantidad.get()
        limite = CANTIDAD_MAXIMA if cantidad_texto == "Max" else int(cantidad_texto)

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

    def _run_search(self, categoria, min_descuento, max_descuento, limite):
        try:
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

    def _show_results(self, chollos):
        self._set_busy(False)
        self.chollos = chollos

        if not chollos:
            self.status_var.set("  No se encontraron chollos con esos filtros.")
            return

        for i, p in enumerate(chollos):
            precio = f"{p.precio_actual:.2f} {p.moneda}" if p.precio_actual else "-"
            self.tree.insert("", tk.END, iid=str(i), values=(f"-{p.descuento_porcentaje}%", p.titulo, precio))

        self.status_var.set(f"  {len(chollos)} chollos encontrados.")

    def _show_error(self, mensaje: str):
        self._set_busy(False)
        self.status_var.set("  Error en la búsqueda.")
        messagebox.showerror("Error", mensaje)

    def abrir_en_amazon(self):
        """Abre en el navegador la página del producto seleccionado."""
        if not self.producto_seleccionado or not self.producto_seleccionado.url_afiliado:
            messagebox.showwarning("Aviso", "Selecciona antes un producto de la lista.")
            return
        webbrowser.open(self.producto_seleccionado.url_afiliado)

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

        self.keepa_label.config(image='', text="Cargando gráfica Keepa...")
        thread = threading.Thread(target=self._load_keepa_graph, args=(producto.asin,))
        thread.daemon = True
        thread.start()

    def _load_keepa_graph(self, asin: str):
        try:
            url = KEEPA_GRAPH_URL.format(asin=asin)
            response = requests.get(url, headers=KEEPA_HEADERS, timeout=15)
            response.raise_for_status()

            img = Image.open(io.BytesIO(response.content))
            img.thumbnail((440, 300))
            photo = ImageTk.PhotoImage(img)

            self.root.after(0, self._set_keepa_image, photo)
        except Exception:
            self.root.after(0, lambda: self.keepa_label.config(image='', text="No se pudo cargar la gráfica Keepa"))

    def _set_keepa_image(self, photo):
        self.keepa_label.config(image=photo, text="")
        # Guardamos la referencia para que el recolector de basura no la borre.
        self.keepa_label.image = photo


def main():
    root = ttk.Window(themename="darkly")
    DealsGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
