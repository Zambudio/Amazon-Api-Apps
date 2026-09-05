"""
Script: Convertir Logo a Icono
Este pequeño script de utilidad toma una imagen en formato PNG y la 
convierte en un archivo .ico compatible con Windows. Esto permite que 
la aplicación tenga su propio icono en la barra de tareas.
"""

from PIL import Image
import os

def convert_png_to_ico(png_path, ico_path):
    """Realiza la conversión de formato PNG a ICO con varios tamaños estándar."""
    if not os.path.exists(png_path):
        print(f"No se encuentra el archivo {png_path}")
        return
    
    img = Image.open(png_path)
    # Generamos el icono incluyendo varios tamaños para que se vea bien en cualquier resolución
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_path, sizes=icon_sizes)
    print(f"Icono guardado en {ico_path}")

if __name__ == "__main__":
    # Por defecto busca 'logo.png' en la raíz y genera 'logo.ico'
    convert_png_to_ico("logo.png", "logo.ico")
