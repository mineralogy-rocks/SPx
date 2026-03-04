# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

ROOT = Path(SPECPATH)

icon_file = ROOT / "data" / "icon.ico"
icon_path = str(icon_file) if icon_file.exists() else None

a = Analysis(
    [str(ROOT / "src" / "gui.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / "data" / "endmembers.xlsx"), "data"),
    ],
    hiddenimports=[
        "scipy",
        "scipy.optimize",
        "scipy.special",
        "scipy.special._cdflib",
        "pysptools",
        "pysptools.spectro",
        "pandas",
        "openpyxl",
        "tqdm",
        "tkinter",
        "numpy",
        "matplotlib",
        "matplotlib.backends.backend_agg",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest",
        "ruff",
        "pre_commit",
    ],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SPx",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    icon=icon_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="SPx",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="SPx.app",
        bundle_identifier="rocks.mineralogy.spx",
    )
