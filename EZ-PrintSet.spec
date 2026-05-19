# -*- mode: python ; coding: utf-8 -*-

import os


icon_path = os.path.abspath("assets/app.ico")
icon_file = icon_path if os.path.exists(icon_path) else None

a = Analysis(
    ["main.py"],
    pathex=[os.path.abspath("src")],
    binaries=[],
    datas=[("profiles", "profiles"), ("assets", "assets")],
    hiddenimports=["win32timezone"],
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
    name="EZ-PrintSet",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon=icon_file,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
