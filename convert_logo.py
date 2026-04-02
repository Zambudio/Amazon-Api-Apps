from PIL import Image
import os

def convert_png_to_ico(png_path, ico_path):
    if not os.path.exists(png_path):
        print(f"No se encuentra el archivo {png_path}")
        return
    
    img = Image.open(png_path)
    # Los iconos suelen tener varios tamaños, pero 256 es el máximo estándar
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_path, sizes=icon_sizes)
    print(f"Icono guardado en {ico_path}")

if __name__ == "__main__":
    convert_png_to_ico("logo.png", "logo.ico")
