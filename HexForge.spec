# -*- mode: python ; coding: utf-8 -*-
<<<<<<< HEAD
import os

src_dir = os.path.abspath('src')

a = Analysis(
    ['src/main.py'],
    pathex=[src_dir],
    binaries=[],
    datas=[('texture_cache/*.png', 'texture_cache')],
=======


a = Analysis(
    ['src\\main.py'],
    pathex=[],
    binaries=[],
    datas=[],
>>>>>>> 7d92dc4dbe289288da131eadc2e39b62d6622ba5
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
<<<<<<< HEAD
)

=======
    optimize=0,
)
>>>>>>> 7d92dc4dbe289288da131eadc2e39b62d6622ba5
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='HexForge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
<<<<<<< HEAD
    upx=False,
=======
    upx=True,
>>>>>>> 7d92dc4dbe289288da131eadc2e39b62d6622ba5
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
