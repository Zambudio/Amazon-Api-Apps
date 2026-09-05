@echo off
rem Rebuild del BuscarChollos.exe tras cambios en el buscador de chollos.
rem Uso: doble clic o desde terminal. Debe ejecutarse desde la raiz del proyecto.
cd /d "%~dp0"
py -m PyInstaller BuscarChollos.spec --noconfirm
if errorlevel 1 (
    echo.
    echo [ERROR] Fallo al construir BuscarChollos.exe
    pause
    exit /b 1
)
echo.
echo [OK] BuscarChollos.exe generado en dist\BuscarChollos\BuscarChollos.exe
pause
