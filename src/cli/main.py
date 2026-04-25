"""
Herramienta CLI: Generador de Posts
Este script permite generar un post de Telegram directamente desde la consola 
sin abrir la interfaz gráfica. Es ideal para pruebas rápidas o para integrar 
en otros scripts automatizados.
"""

import sys
import argparse
import os

# Asegurar que se puede importar independientemente de cómo se llame al script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.use_cases.generate_post import GeneratePostUseCase
from src.config.settings import Config

def main():
    parser = argparse.ArgumentParser(description="Generador de Posts para Telegram desde Amazon.")
    parser.add_argument("url_o_asin", help="URL de Amazon o ASIN del producto.")
    
    args = parser.parse_args()
    
    print(f"Iniciando procesamiento para: {args.url_o_asin}...")
    
    # Instanciamos el caso de uso principal
    use_case = GeneratePostUseCase()
    
    # Ejecutamos el flujo de generación
    resultado = use_case.execute(args.url_o_asin)
    mensaje = resultado.get("text")
    
    if mensaje:
        print("\n" + "="*50)
        print("=== MENSAJE GENERADO PARA TELEGRAM ===")
        print("="*50 + "\n")
        print(mensaje)
    else:
        print("\n[!] No se pudo generar el mensaje. Revisa los errores anteriores.")
        sys.exit(1)

if __name__ == "__main__":
    main()
