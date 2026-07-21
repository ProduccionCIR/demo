# -*- mode: python ; coding: utf-8 -*-
import os
import streamlit
from PyInstaller.utils.hooks import copy_metadata

st_main_path = os.path.dirname(streamlit.__file__)

block_cipher = None

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('main.py', '.'),
        ('admin.py', '.'),
        ('auth.py', '.'),
        ('clientes.py', '.'),
        ('configuracion.py', '.'),
        ('contabilidad.py', '.'),
        ('cotizaciones.py', '.'),
        ('database.py', '.'),
        ('inventario.py', '.'),
        ('utilidades.py', '.'),
        ('ventas.py', '.'),
        (os.path.join(st_main_path, 'runtime'), 'streamlit/runtime'),
        (os.path.join(st_main_path, 'static'), 'streamlit/static'),
    ] + copy_metadata('streamlit'),
    hiddenimports=['streamlit', 'pandas', 'pyarrow', 'weasyprint'], # <-- ¡Agregamos 'weasyprint' aquí!
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='RAV_System',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # <-- Lo cambiamos a False para que ya NO se abra la ventana negra fea por detrás
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RAV_System',
)