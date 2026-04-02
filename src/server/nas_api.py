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

DB_DIR = "nas_data"
DB_FILE = f"{DB_DIR}/borradores.db"
IMG_DIR = f"{DB_DIR}/images"

os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

def init_db():
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
    """Hilo secundario que revisa la BD cada minuto y publica si es la hora."""
    print("🤖 Iniciando Motor de Publicación en Segundo Plano...")
    
    # Instanciamos el publicador general
    try:
        publisher = PublisherService()
    except Exception as e:
        print(f"❌ Error al iniciar PublisherService en NAS: {e}")
        return

    while True:
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            # Hora actual exacta del NAS
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Buscar todos los que están 'pending' y cuya hora ya es pasada o igual a la actual
            c.execute("SELECT id, text, target, photo_url FROM posts WHERE status='pending' AND schedule_time <= ?", (now_str,))
            rows = c.fetchall()
            
            for row in rows:
                p_id, text, target, photo_url = row
                print(f"🚀 Publicando Post ID {p_id} programado para {now_str} en {target}...")
                
                try:
                    if target == "main":
                        publisher.publish_to_main(text, photo_url)
                    else:
                        publisher.publish_to_admin(text, photo_url)
                    
                    c.execute("UPDATE posts SET status='published' WHERE id=?", (p_id,))
                    print(f"✅ Post ID {p_id} Publicado con Éxito.")
                except Exception as e:
                    print(f"❌ Error publicando Post ID {p_id}: {e}")
                    c.execute("UPDATE posts SET status='error' WHERE id=?", (p_id,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ Error Crítico en el Daemon de base de datos: {e}")
            
        # Esperamos 60 segundos hasta la próxima comprobación
        time.sleep(60)

# Lanzar el guardián del tiempo
threading.Thread(target=publisher_daemon, daemon=True).start()


@app.post("/api/schedule")
async def schedule_post(
    text: str = Form(...),
    target: str = Form(...),
    schedule_time: str = Form(...),  # Formato YYYY-MM-DD HH:MM:00
    photo_url: str = Form(""),
    photo: UploadFile = File(None)
):
    final_photo_url = photo_url
    
    # Si el cliente (Windows) envía una foto física, la guardamos en el NAS
    if photo and photo.filename:
        file_ext = photo.filename.split('.')[-1]
        timestamp = int(time.time())
        file_path = f"{IMG_DIR}/{timestamp}.{file_ext}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
            
        final_photo_url = os.path.abspath(file_path)

    # Insertamos en la BD usando hora UTC local del NAS
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO posts (text, target, photo_url, schedule_time, status) VALUES (?, ?, ?, ?, 'pending')",
              (text, target, final_photo_url, schedule_time))
    conn.commit()
    conn.close()
    
    return {"status": "ok", "message": "Publicación guardada y programada en el NAS"}

@app.get("/api/status")
async def get_status():
    return {"status": "El Servidor NAS de BuenChollo está vivo y esperando chollos."}
