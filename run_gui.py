import os
import sys

# Asegurar que estamos en el directorio base correcto
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.ui.main_gui import main

if __name__ == "__main__":
    main()
