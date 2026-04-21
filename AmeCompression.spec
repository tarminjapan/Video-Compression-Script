# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

PROJECT_ROOT = Path(SPECPATH)
VIDEO_COMPRESSOR = PROJECT_ROOT / "video_compressor"

a = Analysis(
    [str(VIDEO_COMPRESSOR / "__main__.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[
        (str(VIDEO_COMPRESSOR / "gui" / "i18n" / "en.json"), "video_compressor/gui/i18n"),
        (str(VIDEO_COMPRESSOR / "gui" / "i18n" / "ja.json"), "video_compressor/gui/i18n"),
    ],
    hiddenimports=[
        "video_compressor",
        "customtkinter",
    ] + collect_submodules("video_compressor.gui"),
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="AmeCompression",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(PROJECT_ROOT / "assets" / "icon.ico") if (PROJECT_ROOT / "assets" / "icon.ico").exists() else None,
)
