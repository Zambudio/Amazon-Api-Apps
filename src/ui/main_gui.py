"""
Interfaz Gráfica Principal (GUI)
Este archivo define la ventana que ve el usuario. Está construido con Tkinter 
y permite pegar un enlace de Amazon, previsualizar el mensaje, elegir fotos, 
añadir categorías y publicar o programar el post con un solo clic.
"""

import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox
import threading
import sys
import os
import io
import requests
from PIL import Image, ImageTk
from tkinter import filedialog

# Asegurar que Python encuentre los módulos en la carpeta 'src'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.use_cases.generate_post import GeneratePostUseCase
from src.services.publisher_service import PublisherService
from src.config.settings import Config
from src.integrations.storage.json_category_repository import JsonCategoryRepository
from src.use_cases.get_categories_for_ui import GetCategoriesForUIUseCase
from src.use_cases.upsert_categories_from_post import UpsertCategoriesFromPostUseCase
from src.domain.hashtag_rules import normalize_hashtag

class AppGUI:
    """
    Clase principal que dibuja la interfaz y maneja los eventos de los botones.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Generador de Ofertas para Telegram")
        self.root.geometry("1400x820")
        self.root.minsize(1100, 750)
        
        # Configuración de iconos y servicios iniciales
        try:
            ico_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')), "logo.ico")
            if os.path.exists(ico_path):
                self.root.iconbitmap(ico_path)
        except Exception:
            pass
        
        # Casos de uso: Lógica de negocio que usará la interfaz
        self.use_case = GeneratePostUseCase()
        try:
            self.publisher = PublisherService()
        except Exception:
            self.publisher = None

        self.category_repository = JsonCategoryRepository(Config.CATEGORIES_FILE_PATH)
        self.get_categories_use_case = GetCategoriesForUIUseCase(self.category_repository)
        self.upsert_categories_use_case = UpsertCategoriesFromPostUseCase(self.category_repository)
        
        self._build_ui()

    def _build_ui(self):
        """Dibuja todos los elementos visuales (botones, textos, imágenes)."""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # --- CABECERA (Logo y Título) ---
        header_frame = ttk.Frame(main_frame, bootstyle="secondary")
        header_frame.pack(fill=tk.X, pady=(0, 20), ipady=10)
        
        logo_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')), "logo.png")
        self.logo_img = None
        content_header = ttk.Frame(header_frame, bootstyle="secondary")
        content_header.pack(expand=True)

        if os.path.exists(logo_path):
            try:
                logo_img_raw = Image.open(logo_path)
                logo_img_raw.thumbnail((80, 80))
                self.logo_img = ImageTk.PhotoImage(logo_img_raw)
                ttk.Label(content_header, image=self.logo_img, bootstyle="inverse-secondary").pack(side=tk.LEFT, padx=20)
            except Exception:
                pass

        text_header_frame = ttk.Frame(content_header, bootstyle="secondary")
        text_header_frame.pack(side=tk.LEFT)
        ttk.Label(text_header_frame, text="🚀 PUBLICADOR DE CHOLLOS", font=("Segoe UI", 20, "bold"), bootstyle="inverse-secondary").pack(anchor="w")
        ttk.Label(text_header_frame, text="Gestión inteligente de ofertas para Telegram", font=("Segoe UI", 10), bootstyle="inverse-secondary").pack(anchor="w")
        
        # --- ENTRADA DE DATOS (URL Amazon) ---
        provider_frame = ttk.LabelFrame(main_frame, text=" Plataforma: Amazon ")
        provider_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(provider_frame, text="Introduce la URL o ASIN del producto:").pack(anchor="w", pady=(0, 5))
        input_frame = ttk.Frame(provider_frame)
        input_frame.pack(fill=tk.X)
        
        self.url_entry = ttk.Entry(input_frame, font=("Segoe UI", 11), bootstyle="primary")
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.btn_generate = ttk.Button(input_frame, text="➔ Extraer y Generar", command=self.start_generation, bootstyle="primary")
        self.btn_generate.pack(side=tk.RIGHT)
        
        self.root.bind('<Return>', lambda event: self.start_generation())
        
        # --- CUERPO (Edición de texto y Previsualización de imagen) ---
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        result_frame = ttk.LabelFrame(content_frame, text=" Mensaje Formateado (Edita el contenido antes de enviar) ")
        result_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.result_text = tk.Text(result_frame, wrap=tk.WORD, height=10, font=("Segoe UI", 12), padx=15, pady=15, spacing1=5, spacing2=2)
        scroll_y = ttk.Scrollbar(result_frame, orient="vertical", command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scroll_y.set)
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Panel de Imagen
        self.image_frame = ttk.LabelFrame(content_frame, text=" Imagen ", width=420)
        self.image_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.image_frame.pack_propagate(False)
        self.img_label = ttk.Label(self.image_frame, text="Sin imagen")
        self.img_label.pack(pady=10, expand=True)
        
        img_controls = ttk.Frame(self.image_frame)
        img_controls.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Button(img_controls, text="◀", width=5, command=self.prev_image, bootstyle="link").pack(side=tk.LEFT)
        self.img_idx_label = ttk.Label(img_controls, text="0 / 0", font=("Segoe UI", 10, "bold"))
        self.img_idx_label.pack(side=tk.LEFT, expand=True)
        ttk.Button(img_controls, text="▶", width=5, command=self.next_image, bootstyle="link").pack(side=tk.RIGHT)
        ttk.Button(self.image_frame, text="Subir propia foto", command=self.upload_custom_image, bootstyle="outline-warning").pack(fill=tk.X, pady=(15,0))
        
        # --- PUBLICACIÓN DIRECTA ---
        direct_actions_frame = ttk.Frame(main_frame)
        direct_actions_frame.pack(pady=(10, 5), fill=tk.X)
        ttk.Label(direct_actions_frame, text="Canal Destino:").pack(side=tk.LEFT, padx=5)
        self.combo_direct_target = ttk.Combobox(direct_actions_frame, values=["Canal Pruebas Admin", "Canal BuenChollo Tech OFICIAL"], state="readonly", width=30, bootstyle="success")
        self.combo_direct_target.current(0)
        self.combo_direct_target.pack(side=tk.LEFT, padx=5)
        self.btn_publish = ttk.Button(direct_actions_frame, text="🚀 Publicar AHORA", command=self.start_publish_to_channel, bootstyle="success")
        self.btn_publish.pack(side=tk.RIGHT, padx=5, expand=True, fill=tk.X)

        # --- GESTIÓN DE CATEGORÍAS ---
        category_frame = ttk.LabelFrame(main_frame, text=" Categorías del Canal ")
        category_frame.pack(fill=tk.X, pady=(5, 10))
        ttk.Label(category_frame, text="Categoría existente:").pack(side=tk.LEFT, padx=(8, 5), pady=8)
        self.combo_categories = ttk.Combobox(category_frame, state="readonly", width=32)
        self.combo_categories.pack(side=tk.LEFT, padx=5)
        ttk.Label(category_frame, text="o Nueva categoría:").pack(side=tk.LEFT, padx=(12, 5))
        self.entry_new_category = ttk.Entry(category_frame, width=22)
        self.entry_new_category.pack(side=tk.LEFT, padx=5)
        ttk.Button(category_frame, text="Añadir al catálogo", command=self.add_category_to_message, bootstyle="outline-info").pack(side=tk.LEFT, padx=(10, 8))
        
        # --- PROGRAMACIÓN NAS (Ocultable) ---
        self.nas_container = ttk.Frame(main_frame)
        self.nas_container.pack(fill=tk.X, pady=(5, 0))
        self.show_nas_var = tk.BooleanVar(value=False)
        self.btn_toggle_nas = ttk.Checkbutton(self.nas_container, text="➕ Mostrar opciones de Programación en NAS", variable=self.show_nas_var, command=self.toggle_nas_frame, bootstyle="secondary")
        self.btn_toggle_nas.pack(anchor="w", pady=(0, 5))

        self.schedule_frame = ttk.LabelFrame(self.nas_container, text=" Programar Publicación (NAS) ")
        ttk.Label(self.schedule_frame, text="Canal:").pack(side=tk.LEFT, padx=5)
        self.combo_target = ttk.Combobox(self.schedule_frame, values=["Canal Pruebas Admin", "Canal BuenChollo Tech OFICIAL"], state="readonly", width=25)
        self.combo_target.current(0)
        self.combo_target.pack(side=tk.LEFT, padx=5)
        
        from datetime import datetime
        now = datetime.now()
        ttk.Label(self.schedule_frame, text="Fecha:").pack(side=tk.LEFT, padx=(10, 5))
        self.entry_date = ttk.Entry(self.schedule_frame, width=6)
        self.entry_date.insert(0, now.strftime("%d/%m"))
        self.entry_date.pack(side=tk.LEFT, padx=5)
        ttk.Label(self.schedule_frame, text="Hora:").pack(side=tk.LEFT, padx=(10, 5))
        self.entry_time = ttk.Entry(self.schedule_frame, width=6)
        self.entry_time.insert(0, now.strftime("%H:%M"))
        self.entry_time.pack(side=tk.LEFT, padx=5)
        ttk.Button(self.schedule_frame, text="☁️ Programar en NAS", command=self.start_schedule_to_nas, bootstyle="outline-secondary").pack(side=tk.RIGHT, padx=5)
        
        self.status_var = tk.StringVar(value="  Esperando entrada...")
        ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w", padding=2).pack(side=tk.BOTTOM, fill=tk.X)
        self.refresh_categories()

    # --- LÓGICA DE LA INTERFAZ ---

    def set_status(self, text, block_ui=False):
        """Actualiza el texto de la barra inferior y bloquea/desbloquea botones."""
        self.status_var.set(f"  {text}")
        state = 'disabled' if block_ui else '!disabled'
        widgets = [self.btn_generate, self.url_entry, self.btn_publish, self.combo_direct_target, self.btn_schedule, self.combo_categories, self.entry_new_category, self.btn_add_category]
        for w in widgets: w.state([state])
        self.root.update_idletasks()

    def start_generation(self):
        """Inicia el proceso de extracción de Amazon en un hilo separado."""
        url = self.url_entry.get().strip()
        if not url: return
        self.set_status("Consultando Amazon...", block_ui=True)
        threading.Thread(target=self._run_use_case, args=(url,), daemon=True).start()

    def _run_use_case(self, url):
        try:
            result = self.use_case.execute(url)
            self.root.after(0, self._show_result, result)
        except Exception as e:
            self.root.after(0, self._show_error, e)

    def _show_result(self, result):
        self.set_status("Listo para enviar", block_ui=False)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, result.get("text", ""))
        product = result.get("product")
        self.all_images = ([product.imagen_principal] if product.imagen_principal else []) + (product.imagenes_extra or [])
        self.current_img_idx = 0
        self.update_image_preview()

    def update_image_preview(self):
        """Carga y redimensiona la imagen seleccionada para mostrarla en la ventana."""
        if not self.all_images:
            self.img_label.config(image='', text="Sin imagen")
            return
        url = self.all_images[self.current_img_idx]
        self.img_idx_label.config(text=f"{self.current_img_idx + 1} / {len(self.all_images)}")
        threading.Thread(target=self._load_and_display_image, args=(url,), daemon=True).start()

    def _load_and_display_image(self, path):
        try:
            img = Image.open(io.BytesIO(requests.get(path).content)) if path.startswith('http') else Image.open(path)
            img.thumbnail((380, 380))
            photo = ImageTk.PhotoImage(img)
            self.root.after(0, self._set_image_in_label, photo)
        except Exception:
            self.root.after(0, lambda: self.img_label.config(text="Error imagen"))

    def _set_image_in_label(self, photo):
        self.img_label.config(image=photo, text="")
        self.img_label.image = photo

    def start_publish_to_channel(self):
        """Envía el post directamente a Telegram."""
        target = "main" if "OFICIAL" in self.combo_direct_target.get() else "admin"
        texto = self.result_text.get(1.0, tk.END).strip()
        photo = self.all_images[self.current_img_idx] if self.all_images else None
        self.set_status("Publicando...", block_ui=True)
        threading.Thread(target=self._run_publish, args=(texto, photo, target), daemon=True).start()

    def _run_publish(self, texto, photo, target):
        try:
            if target == "main": self.publisher.publish_to_main(texto, photo)
            else: self.publisher.publish_to_admin(texto, photo)
            self.root.after(0, self._publish_success)
        except Exception as e: self.root.after(0, self._show_error, e)

    def _publish_success(self):
        self.set_status("¡Publicado!", block_ui=False)
        messagebox.showinfo("Éxito", "Chollo publicado correctamente.")

    def start_schedule_to_nas(self):
        """Envía el post al servidor NAS para que se publique en el futuro."""
        texto = self.result_text.get(1.0, tk.END).strip()
        target = "main" if "OFICIAL" in self.combo_target.get() else "admin"
        from datetime import datetime
        try:
            d, m = self.entry_date.get().split('/')
            h, mi = self.entry_time.get().split(':')
            schedule_time = f"{datetime.now().year}-{m}-{d} {h}:{mi}:00"
            photo = self.all_images[self.current_img_idx] if self.all_images else ""
            self.set_status("Enviando al NAS...", block_ui=True)
            threading.Thread(target=self._send_to_nas, args=(texto, target, schedule_time, photo), daemon=True).start()
        except Exception: messagebox.showerror("Error", "Revisa el formato de fecha (DD/MM) y hora (HH:MM)")

    def _send_to_nas(self, text, target, schedule_time, photo_url):
        nas_ip = os.getenv("NAS_SERVER_URL", "http://192.168.1.100:8000")
        try:
            payload = {"text": text, "target": target, "schedule_time": schedule_time}
            if photo_url.startswith('http'):
                payload["photo_url"] = photo_url
                requests.post(f"{nas_ip}/api/schedule", data=payload, timeout=20)
            else:
                with open(photo_url, 'rb') as f:
                    requests.post(f"{nas_ip}/api/schedule", data=payload, files={'photo': f}, timeout=30)
            self.root.after(0, lambda: self.set_status("Programado en NAS", block_ui=False))
            self.root.after(0, lambda: messagebox.showinfo("NAS", "¡Programado con éxito!"))
        except Exception as e: self.root.after(0, self._show_error, e)

    # ... (Otros métodos auxiliares como toggle_nas_frame, refresh_categories, etc.)

def main():
    root = ttk.Window(themename="darkly")
    AppGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
