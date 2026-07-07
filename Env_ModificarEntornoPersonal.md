#Activar .venv_trabajo:
.\.venv_trabajo\Scripts\Activate.ps1

#Desactivar:
deactivate

En tu PC personal, cuando lo necesites, haces lo mismo pero con .venv_casa:

python -m venv .venv_casa
.\.venv_casa\Scripts\Activate.ps1
pip install -r requirements.txt
python run_gui.py
Ninguno de los dos irá a git. El .venv roto que ya tienes puedes borrarlo cuando quieras con:

Remove-Item -Recurse -Force .venv