"""
Servidor de Programación (NAS API)
Este archivo es el 'Cerebro' que se ejecuta en el servidor o NAS (Synology). 
Recibe las publicaciones programadas desde la interfaz de Windows, las guarda 
en una base de datos local y un 'guardián' (daemon) las publica automáticamente 
en Telegram cuando llega la hora acordada.
"""

import os
import sys
import time
import sqlite3
import threading
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form
import shutil

# Aseguramos que el servidor pueda importar los módulos del proyecto raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.services.publisher_service import PublisherService
from src.config.settings import Config

app = FastAPI(title="BuenChollo NAS Scheduler API")

# Directorios para guardar la base de datos y las imágenes subidas
DB_DIR = "nas_data"
DB_FILE = f"{DB_DIR}/borradores.db"
IMG_DIR = f"{DB_DIR}/images"

os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

def init_db():
    """Crea la tabla de posts programados si no existe."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT,
                    target TEXT,
                    photo_url TEXT,
                    schedule_time TEXT,
                    status TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

def publisher_daemon():
    """
    Hilo secundario (Guardián) que se despierta cada minuto. 
    Busca en la base de datos si hay algún post cuya hora de publicación 
    ya haya llegado y lo envía a Telegram.
    """
    print("🤖 Iniciando Motor de Publicación en Segundo Plano...")
    
    try:
        publisher = PublisherService()
    except Exception as e:
        print(f"❌ Error al iniciar PublisherService en NAS: {e}")
        return

    while True:
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            # Obtenemos la hora actual del servidor
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Buscamos posts pendientes que ya deban publicarse
            c.execute("SELECT id, text, target, photo_url FROM posts WHERE status='pending' AND schedule_time <= ?", (now_str,))
            rows = c.fetchall()
            
            for row in rows:
                p_id, text, target, photo_url = row
                print(f"🚀 Publicando Post ID {p_id}...")
                
                try:
                    # Publicamos según el canal elegido
                    if target == "main":
                        publisher.publish_to_main(text, photo_url)
                    else:
                        publisher.publish_to_admin(text, photo_url)
                    
                    c.execute("UPDATE posts SET status='published' WHERE id=?", (p_id,))
                except Exception as e:
                    print(f"❌ Error publicando Post ID {p_id}: {e}")
                    c.execute("UPDATE posts SET status='error' WHERE id=?", (p_id,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ Error Crítico: {e}")
            
        # Esperamos 60 segundos antes de volver a comprobar
        time.sleep(60)

# Lanzamos el guardián en un hilo separado para que no bloquee la API
threading.Thread(target=publisher_daemon, daemon=True).start()


@app.post("/api/schedule")
async def schedule_post(
    text: str = Form(...),
    target: str = Form(...),
    schedule_time: str = Form(...),  # Formato: YYYY-MM-DD HH:MM:00
    photo_url: str = Form(""),
    photo: UploadFile = File(None)
):
    """
    Endpoint de la API que recibe un nuevo chollo para programar. 
    Puede recibir una URL de imagen o el archivo físico de la imagen.
    """
    final_photo_url = photo_url
    
    # Si el usuario subió una foto propia, la guardamos localmente en el NAS
    if photo and photo.filename:
        file_ext = photo.filename.split('.')[-1]
        timestamp = int(time.time())
        file_path = f"{IMG_DIR}/{timestamp}.{file_ext}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
            
        final_photo_url = os.path.abspath(file_path)

    # Guardamos todo en la base de datos como 'pending' (pendiente)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO posts (text, target, photo_url, schedule_time, status) VALUES (?, ?, ?, ?, 'pending')",
              (text, target, final_photo_url, schedule_time))
    conn.commit()
    conn.close()
    
    return {"status": "ok", "message": "Publicación programada correctamente"}

@app.get("/api/status")
async def get_status():
    """Endpoint simple para comprobar que el servidor está encendido."""
    return {"status": "Servidor NAS de BuenChollo activo."}
