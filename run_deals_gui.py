"""
Lanzador de la GUI de Búsqueda de Chollos
Este archivo es el punto de inicio para ejecutar la ventana de búsqueda de
chollos, independiente de la GUI de publicación (run_gui.py). Se encarga de
configurar las rutas necesarias para que Python encuentre los módulos del
proyecto y abre la ventana principal para el usuario.
"""

import sys
import os

# Asegurar que el directorio raíz esté en el path para poder importar desde 'src'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ui.deals_gui import main

if __name__ == "__main__":
    main()
