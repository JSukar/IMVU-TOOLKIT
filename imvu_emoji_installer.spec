# PyInstaller spec for IMVU Emoji Patch Installer (Windows .exe)
# Build: pyinstaller --clean imvu_emoji_installer.spec
# Output: dist/IMVU-Emoji-Installer/ (onedir — fewer AV false positives than onefile)

import os

ROOT = os.path.abspath(SPECPATH)
ICON = os.path.join(ROOT, "assets", "imvu-toolkit-logo.ico")
VERSION_INFO = os.path.join(ROOT, "assets", "installer_version_info.txt")

datas = [
    (os.path.join(ROOT, "emoji_assets", "js"), os.path.join("emoji_assets", "js")),
    (
        os.path.join(ROOT, "library_decompiled_structured", "im", "common.py"),
        os.path.join("library_decompiled_structured", "im"),
    ),
]

a = Analysis(
    [os.path.join(ROOT, "imvu_emoji_installer.py")],
    pathex=[ROOT, os.path.join(ROOT, "src")],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "imvu_toolkit",
        "imvu_toolkit.paths",
        "imvu_toolkit.imvu_process",
        "imvu_toolkit.zip_utils",
        "imvu_toolkit.patches.emoji.constants",
        "imvu_toolkit.patches.emoji.transforms",
        "imvu_toolkit.patches.emoji.patch",
    ],
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
    name="IMVU-Emoji-Installer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON if os.path.exists(ICON) else None,
    version=VERSION_INFO if os.path.exists(VERSION_INFO) else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="IMVU-Emoji-Installer",
)
