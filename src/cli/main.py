import sys
import argparse

# Asegurar que se puede importar independientemente de cómo se llame al script
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.use_cases.generate_post import GeneratePostUseCase
from src.config.settings import Config  # Forzar carga de variables de entorno tempranamente

def main():
    parser = argparse.ArgumentParser(description="Generador de Posts para Telegram desde Amazon.")
    parser.add_argument("url_o_asin", help="URL de Amazon o ASIN del producto.")
    
    args = parser.parse_args()
    
    print(f"Iniciando procesamiento para: {args.url_o_asin}...")
    
    # Instanciamos el caso de uso
    use_case = GeneratePostUseCase()
    
    # Ejecutamos el flujo principal
    mensaje = use_case.execute(args.url_o_asin)
    
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
