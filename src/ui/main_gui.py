import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
import threading
import sys
import os
import io
import requests
from PIL import Image, ImageTk
from tkinter import filedialog

# Asegurar importaciones relativas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.use_cases.generate_post import GeneratePostUseCase
from src.services.publisher_service import PublisherService

class AppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Generador de Ofertas para Telegram")
        self.root.geometry("1400x820")
        self.root.minsize(1100, 750)
        
        # Intentar poner el icono de la ventana (necesita formato .ico en Windows)
        try:
            ico_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')), "logo.ico")
            if os.path.exists(ico_path):
                self.root.iconbitmap(ico_path)
        except Exception as e:
            print(f"No se pudo cargar el icono de la ventana: {e}")
        
        # Iniciar dominio y publicación
        self.use_case = GeneratePostUseCase()
        try:
            self.publisher = PublisherService()
        except:
            self.publisher = None
        
        self._build_ui()

    def _build_ui(self):
        # Marco principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Título y Cabecera con estilo más moderno
        header_frame = ttk.Frame(main_frame, bootstyle="secondary")
        header_frame.pack(fill=tk.X, pady=(0, 20), ipady=10)
        
        # Intentar cargar el logo desde el directorio raíz
        logo_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')), "logo.png")
        self.logo_img = None
        
        # Contenedor para título y logo dentro de la cabecera
        content_header = ttk.Frame(header_frame, bootstyle="secondary")
        content_header.pack(expand=True)

        if os.path.exists(logo_path):
            try:
                logo_img_raw = Image.open(logo_path)
                logo_img_raw.thumbnail((80, 80)) # Tamaño elegante para el logo
                self.logo_img = ImageTk.PhotoImage(logo_img_raw)
                
                logo_lbl = ttk.Label(content_header, image=self.logo_img, bootstyle="inverse-secondary")
                logo_lbl.pack(side=tk.LEFT, padx=20)
            except Exception as e:
                print(f"No se pudo cargar el logo: {e}")

        # Contenedor de textos (Título y subtítulo)
        text_header_frame = ttk.Frame(content_header, bootstyle="secondary")
        text_header_frame.pack(side=tk.LEFT)

        title_lbl = ttk.Label(text_header_frame, text="🚀 PUBLICADOR DE CHOLLOS", font=("Segoe UI", 20, "bold"), bootstyle="inverse-secondary")
        title_lbl.pack(anchor="w")
        
        subtitle_lbl = ttk.Label(text_header_frame, text="Gestión inteligente de ofertas para Telegram", font=("Segoe UI", 10), bootstyle="inverse-secondary")
        subtitle_lbl.pack(anchor="w")
        
        # Marco para controles del proveedor (Amazon por ahora, futuro extensible)
        provider_frame = ttk.LabelFrame(main_frame, text=" Plataforma: Amazon ")
        provider_frame.pack(fill=tk.X, pady=(0, 15))
        
        lbl_inst = ttk.Label(provider_frame, text="Introduce la URL o ASIN del producto:")
        lbl_inst.pack(anchor="w", pady=(0, 5))
        
        # Contenedor horizontal para el input y botón
        input_frame = ttk.Frame(provider_frame)
        input_frame.pack(fill=tk.X)
        
        self.url_entry = ttk.Entry(input_frame, font=("Segoe UI", 11), bootstyle="primary")
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.btn_generate = ttk.Button(input_frame, text="➔ Extraer y Generar", command=self.start_generation, bootstyle="primary")
        self.btn_generate.pack(side=tk.RIGHT)
        
        # Bind enter key
        self.root.bind('<Return>', lambda event: self.start_generation())
        
        # Marco para el resultado y la previsualización de imagen
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        result_frame = ttk.LabelFrame(content_frame, text=" Mensaje Formateado (Edita el contenido antes de enviar) ")
        result_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Text area con scroll y diseño mejorado para lectura
        self.result_text = tk.Text(
            result_frame, 
            wrap=tk.WORD, 
            height=10, 
            font=("Segoe UI", 12),
            padx=15, pady=15, spacing1=5, spacing2=2
        )
        scroll_y = ttk.Scrollbar(result_frame, orient="vertical", command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scroll_y.set)
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Panel de Imagen (Más grande)
        self.image_frame = ttk.LabelFrame(content_frame, text=" Imagen ", width=420)
        self.image_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.image_frame.pack_propagate(False)
        
        self.img_label = ttk.Label(self.image_frame, text="Sin imagen")
        self.img_label.pack(pady=10, expand=True)
        
        img_controls = ttk.Frame(self.image_frame)
        img_controls.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.btn_prev_img = ttk.Button(img_controls, text="◀", width=5, command=self.prev_image, bootstyle="link")
        self.btn_prev_img.pack(side=tk.LEFT)
        
        self.img_idx_label = ttk.Label(img_controls, text="0 / 0", font=("Segoe UI", 10, "bold"))
        self.img_idx_label.pack(side=tk.LEFT, expand=True)
        
        self.btn_next_img = ttk.Button(img_controls, text="▶", width=5, command=self.next_image, bootstyle="link")
        self.btn_next_img.pack(side=tk.RIGHT)

        ttk.Button(self.image_frame, text="Subir propia foto", command=self.upload_custom_image, bootstyle="outline-warning").pack(fill=tk.X, pady=(15,0))
        
        # Contenedor de acciones (Botones envío directo)
        direct_actions_frame = ttk.Frame(main_frame)
        direct_actions_frame.pack(pady=(10, 5), fill=tk.X)
        
        lbl_target_direct = ttk.Label(direct_actions_frame, text="Canal Destino:")
        lbl_target_direct.pack(side=tk.LEFT, padx=5)
        
        self.combo_direct_target = ttk.Combobox(direct_actions_frame, values=["Canal Pruebas Admin", "Canal BuenChollo Tech OFICIAL"], state="readonly", width=30, bootstyle="success")
        self.combo_direct_target.current(0) # Por defecto al canal de pruebas (Admin)
        self.combo_direct_target.pack(side=tk.LEFT, padx=5)
        
        self.btn_publish = ttk.Button(direct_actions_frame, text="🚀 Publicar AHORA", command=self.start_publish_to_channel, bootstyle="success")
        self.btn_publish.pack(side=tk.RIGHT, padx=5, expand=True, fill=tk.X)
        
        # Contenedor padre para ocultar/mostrar NAS
        self.nas_container = ttk.Frame(main_frame)
        self.nas_container.pack(fill=tk.X, pady=(5, 0))
        
        self.show_nas_var = tk.BooleanVar(value=False)
        self.btn_toggle_nas = ttk.Checkbutton(
            self.nas_container, 
            text="➕ Mostrar opciones de Programación en NAS", 
            variable=self.show_nas_var, 
            command=self.toggle_nas_frame,
            bootstyle="secondary"
        )
        self.btn_toggle_nas.pack(anchor="w", pady=(0, 5))

        # Panel de Programación en NAS
        self.schedule_frame = ttk.LabelFrame(self.nas_container, text=" Programar Publicación (NAS) ")
        
        lbl_dest = ttk.Label(self.schedule_frame, text="Canal Destino:")
        lbl_dest.pack(side=tk.LEFT, padx=5)
        
        self.combo_target = ttk.Combobox(self.schedule_frame, values=["Canal Pruebas Admin", "Canal BuenChollo Tech OFICIAL"], state="readonly", width=30)
        self.combo_target.current(0) # Por defecto al canal de pruebas (Admin)
        self.combo_target.pack(side=tk.LEFT, padx=5)
        
        from datetime import datetime
        now = datetime.now()
        lbl_date = ttk.Label(self.schedule_frame, text="Fecha (DD/MM):")
        lbl_date.pack(side=tk.LEFT, padx=(15, 5))
        
        self.entry_date = ttk.Entry(self.schedule_frame, width=8)
        self.entry_date.insert(0, now.strftime("%d/%m"))
        self.entry_date.pack(side=tk.LEFT, padx=5)
        
        lbl_time = ttk.Label(self.schedule_frame, text="Hora (HH:MM):")
        lbl_time.pack(side=tk.LEFT, padx=(15, 5))
        
        self.entry_time = ttk.Entry(self.schedule_frame, width=8)
        self.entry_time.insert(0, now.strftime("%H:%M"))
        self.entry_time.pack(side=tk.LEFT, padx=5)
        
        self.btn_schedule = ttk.Button(self.schedule_frame, text="☁️ Enviar al NAS para Programar", command=self.start_schedule_to_nas, bootstyle="outline-secondary")
        self.btn_schedule.pack(side=tk.RIGHT, padx=5)
        
        # Estado de imágenes
        self.current_product = None
        self.all_images = []
        self.current_img_idx = 0
        
        # Barra de estado
        self.status_var = tk.StringVar()
        self.status_var.set("  Esperando entrada...")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w", padding=2)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def toggle_nas_frame(self):
        if self.show_nas_var.get():
            self.schedule_frame.pack(fill=tk.X)
            self.btn_toggle_nas.config(text="➖ Ocultar opciones de Programación en NAS")
        else:
            self.schedule_frame.pack_forget()
            self.btn_toggle_nas.config(text="➕ Mostrar opciones de Programación en NAS")

    def set_status(self, text, block_ui=False):
        self.status_var.set(f"  {text}")
        if block_ui:
            self.btn_generate.state(['disabled'])
            self.url_entry.state(['disabled'])
            self.btn_publish.state(['disabled'])
            self.combo_direct_target.state(['disabled'])
            self.btn_schedule.state(['disabled'])
        else:
            self.btn_generate.state(['!disabled'])
            self.url_entry.state(['!disabled'])
            self.btn_publish.state(['!disabled'])
            self.combo_direct_target.state(['!disabled'])
            self.btn_schedule.state(['!disabled'])
        self.root.update_idletasks() # Forzar dibujado

    def start_generation(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Aviso", "Por favor, introduce una URL o ASIN.")
            return
            
        self.set_status("Consultando información con Amazon SDK...", block_ui=True)
        self.result_text.delete(1.0, tk.END)
        self.img_label.config(text="Cargando...")
        
        # Lanza en un hilo para no congelar la ventana
        thread = threading.Thread(target=self._run_use_case, args=(url,))
        thread.daemon = True
        thread.start()

    def _run_use_case(self, url):
        try:
            result = self.use_case.execute(url)
            self.root.after(0, self._show_result, result)
        except Exception as e:
            self.root.after(0, self._show_error, e)

    def _show_result(self, result):
        self.set_status("Listo para enviar", block_ui=False)
        mensaje = result.get("text")
        product = result.get("product")
        
        self.current_product = product
        
        if mensaje:
            self.result_text.insert(tk.END, mensaje)
            self.status_var.set("  ✔️ Selecciona la imagen y pulsa Publicar.")
            
            # Gestionar imágenes
            self.all_images = []
            if product.imagen_principal:
                self.all_images.append(product.imagen_principal)
            if product.imagenes_extra:
                self.all_images.extend(product.imagenes_extra)
                
            self.current_img_idx = 0
            self.update_image_preview()
        else:
            self.result_text.insert(tk.END, "❌ Error: La API no devolvió información.")
            self.status_var.set("  ❌ Error de extracción.")
            self.img_label.config(text="Sin imagen")

    def update_image_preview(self):
        if not self.all_images:
            self.img_label.config(image='', text="No hay imágenes")
            self.img_idx_label.config(text="0 / 0")
            return
            
        url = self.all_images[self.current_img_idx]
        self.img_idx_label.config(text=f"{self.current_img_idx + 1} / {len(self.all_images)}")
        
        # Lanzar descarga/procesado en hilo separado para que no se congele la ventana
        thread = threading.Thread(target=self._load_and_display_image, args=(url,))
        thread.daemon = True
        thread.start()

    def _load_and_display_image(self, path_or_url):
        try:
            if path_or_url.startswith('http'):
                response = requests.get(path_or_url, timeout=10)
                response.raise_for_status()
                img_data = response.content
                img = Image.open(io.BytesIO(img_data))
            else:
                img = Image.open(path_or_url)
            
            # Redimensionar manteniendo aspecto Ratio (Max 380x380)
            img.thumbnail((380, 380))
            
            # Convertir a formato compatible con Tkinter
            photo = ImageTk.PhotoImage(img)
            
            # Actualizar en el hilo principal
            self.root.after(0, self._set_image_in_label, photo)
            
        except Exception as e:
            print(f"Error cargando imagen: {e}")
            self.root.after(0, lambda: self.img_label.config(image='', text="Error al cargar\nimagen"))

    def _set_image_in_label(self, photo):
        self.img_label.config(image=photo, text="")
        # Importante guardar referencia para que el recolector de basura no borre la imagen
        self.img_label.image = photo

    def next_image(self):
        if self.all_images:
            self.current_img_idx = (self.current_img_idx + 1) % len(self.all_images)
            self.update_image_preview()

    def prev_image(self):
        if self.all_images:
            self.current_img_idx = (self.current_img_idx - 1) % len(self.all_images)
            self.update_image_preview()

    def upload_custom_image(self):
        # Opción simple: pedir una URL o usar un file dialog
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(title="Selecciona una imagen", filetypes=[("Imágenes", "*.jpg *.png *.jpeg *.webp")])
        if file_path:
            # En una fase real, aquí subiríamos el archivo a un host o lo pasaríamos al bot.
            # Como Telegram permite enviar Local Files por POST, marcaremos esta ruta.
            self.all_images.append(file_path)
            self.current_img_idx = len(self.all_images) - 1
            self.update_image_preview()
            messagebox.showinfo("Imagen", "Imagen local añadida a la cola.")

    def _show_error(self, ExceptionObj):
        self.set_status("Error crítico.", block_ui=False)
        messagebox.showerror("Error Interno", f"Fallo:\n{str(ExceptionObj)}")

    # Se ha eliminado el bloque de copy_to_clipboard a petición del usuario.
            
    def start_publish_to_channel(self):
        target_str = self.combo_direct_target.get()
        target = "main" if "OFICIAL" in target_str else "admin"

        texto = self.result_text.get(1.0, tk.END).strip()
        if not texto or texto.startswith("❌"):
            messagebox.showwarning("Aviso", "No hay un chollo válido para enviar.")
            return
            
        nombre_destino = "Canal Principal OFICIAL" if target == "main" else "Canal de Pruebas Admin"
            
        if not self.publisher:
            messagebox.showerror("Error", "El servicio de publicación falló al iniciar. ¿Configuraste TELEGRAM_BOT_TOKEN?")
            return
            
        # Obtener URL de imagen seleccionada
        photo_url = None
        if self.all_images:
            photo_url = self.all_images[self.current_img_idx]
            
        self.set_status(f"Enviando a {nombre_destino}...", block_ui=True)
        
        thread = threading.Thread(target=self._run_publish, args=(texto, photo_url, target))
        thread.daemon = True
        thread.start()
        
    def _run_publish(self, texto, photo_url, target):
        try:
            if target == "main":
                self.publisher.publish_to_main(texto, photo_url=photo_url)
            else:
                self.publisher.publish_to_admin(texto, photo_url=photo_url)
                
            self.root.after(0, self._publish_success)
        except Exception as e:
            self.root.after(0, self._show_error, e)
            
    def _publish_success(self):
        self.set_status("Publicado con éxito", block_ui=False)
        messagebox.showinfo("Éxito", "¡El chollo ha sido publicado correctamente!")
        self.status_var.set("  🚀 Mensaje publicado en el canal.")

    def start_schedule_to_nas(self):
        texto = self.result_text.get(1.0, tk.END).strip()
        if not texto or texto.startswith("❌"):
            messagebox.showwarning("Aviso", "No hay un chollo válido para programar.")
            return

        target_str = self.combo_target.get()
        target = "main" if "OFICIAL" in target_str else "admin"
        
        fecha = self.entry_date.get()
        hora = self.entry_time.get()
        
        # Validar un poco el formato
        if "/" not in fecha or ":" not in hora:
            messagebox.showerror("Error", "Formato de fecha u hora incorrecto. Usa DD/MM y HH:MM")
            return

        # "02/04", "20:00" -> YYYY-MM-DD HH:MM:00
        from datetime import datetime
        year = datetime.now().year
        day, month = fecha.split("/")
        schedule_time_str = f"{year}-{month}-{day} {hora}:00"

        # Obtener URL de imagen seleccionada
        photo_url = ""
        if self.all_images:
            photo_url = self.all_images[self.current_img_idx]

        self.set_status("  ☁️ Enviando al NAS...", block_ui=True)
        
        # Realizamos la petición en segundo plano
        thread = threading.Thread(target=self._send_to_nas, args=(texto, target, schedule_time_str, photo_url))
        thread.daemon = True
        thread.start()

    def _send_to_nas(self, text, target, schedule_time_str, photo_url):
        import requests
        import mimetypes
        from src.config.settings import Config
        import os
        
        nas_ip = os.getenv("NAS_SERVER_URL", "http://192.168.1.100:8000") # IP por defecto si no se configura
        url = f"{nas_ip}/api/schedule"
        
        payload = {
            "text": text,
            "target": target,
            "schedule_time": schedule_time_str
        }
        
        files = {}
        try:
            # Si es un enlace normal de internet (Amazon)
            if photo_url.startswith('http'):
                payload["photo_url"] = photo_url
                response = requests.post(url, data=payload, timeout=20)
            else:
                # Si es una foto local subida por ti, la empaquetamos
                mime = mimetypes.guess_type(photo_url)[0] or 'image/jpeg'
                with open(photo_url, 'rb') as f:
                    files = {'photo': (os.path.basename(photo_url), f, mime)}
                    response = requests.post(url, data=payload, files=files, timeout=30)
                    
            response.raise_for_status()
            
            self.root.after(0, lambda: self.set_status("  ✅ Guardado en el NAS", block_ui=False))
            self.root.after(0, lambda: messagebox.showinfo("Éxito NAS", "¡El Programa ha sido guardado correctamente en tu Synology y se publicará a la hora acordada!"))
            
        except Exception as e:
            self.root.after(0, self._show_error, e)

def main():
    # Usar Window de ttkbootstrap para activar el sistema de temas dinámico
    root = ttk.Window(themename="darkly")
    app = AppGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
