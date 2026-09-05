# -*- mode: python ; coding: utf-8 -*-
import os

# PyInstaller puede ejecutar el spec en un contexto donde __file__ no existe.
SPEC_DIR = os.path.abspath(os.getcwd())
ASSETS_DIR = os.path.join(SPEC_DIR, 'assets')
ASSETS_PNG = os.path.join(ASSETS_DIR, 'logo.png')
ASSETS_ICO = os.path.join(ASSETS_DIR, 'logo.ico')
ROOT_PNG = os.path.join(SPEC_DIR, 'logo.png')
ROOT_ICO = os.path.join(SPEC_DIR, 'logo.ico')
ENV_EXAMPLE = os.path.join(SPEC_DIR, '.env.example')

logo_png_path = ASSETS_PNG if os.path.exists(ASSETS_PNG) else ROOT_PNG
logo_ico_path = ASSETS_ICO if os.path.exists(ASSETS_ICO) else ROOT_ICO

SYS_SITE_PACKAGES = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', 'Python', 'Python314', 'Lib', 'site-packages')

analysis_paths = [SPEC_DIR]
if os.path.isdir(SYS_SITE_PACKAGES):
    analysis_paths.append(SYS_SITE_PACKAGES)

datas = [
    ('src', 'src'),
    ('data', 'data'),
]
if os.path.exists(logo_png_path):
    datas.append((logo_png_path, '.'))
if os.path.exists(ENV_EXAMPLE):
    datas.append((ENV_EXAMPLE, '.'))
if os.path.isdir(ASSETS_DIR):
    datas.append((ASSETS_DIR, 'assets'))

a = Analysis(
    ['run_deals_gui.py'],
    pathex=analysis_paths,
    binaries=[],
    datas=datas,
    hiddenimports=['creatorsapi_python_sdk', 'amazon_creatorsapi'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BuscarChollos',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=logo_ico_path,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BuscarChollos',
)
