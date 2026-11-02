# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_dynamic_libs

datas = [
    ('images', 'images'),
    ('audios_Español', 'audios_Español'),
    ('audios_mazahua', 'audios_mazahua'),
    ('audios_ingles', 'audios_ingles'),
    # Semilla con el catálogo trilingüe definitivo. Al primer arranque se
    # copia a %LOCALAPPDATA%\\LoteriaMazahua, fuera de la carpeta temporal.
    ('loteria_mazahua.sqlite3', '.'),
]
binaries = []
hiddenimports = ['ffpyplayer', 'ffpyplayer.player', 'Pillow', 'pyserial', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'hashlib']
# PyInstaller ya incluye los complementos Qt de los módulos importados. Solo
# se añaden aquí las bibliotecas nativas del reproductor de audio.
binaries += collect_dynamic_libs('ffpyplayer')


a = Analysis(
    ['app_loteria_qt.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    a.binaries,
    a.datas,
    [],
    name='LoteriaMazahua',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['logo.ico'],
)
