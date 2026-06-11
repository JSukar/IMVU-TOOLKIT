# PyInstaller spec for IMVU Antibot Patch Installer (Windows .exe)
# Build: pyinstaller --clean imvu_antibot_installer.spec
# Output: dist/IMVU-Antibot-Installer.exe (standalone onefile GUI)

import os

ROOT = os.path.abspath(SPECPATH)
ICON = os.path.join(ROOT, "assets", "imvu-toolkit-logo.ico")
VERSION_INFO = os.path.join(ROOT, "assets", "antibot_installer_version_info.txt")

datas = [
    (os.path.join(ROOT, "antibot_assets", "js"), os.path.join("antibot_assets", "js")),
    (
        os.path.join(ROOT, "library_decompiled_structured"),
        "library_decompiled_structured",
    ),
    (os.path.join(ROOT, "assets", "imvu-toolkit-logo.png"), os.path.join("assets")),
    (os.path.join(ROOT, "assets", "imvu-toolkit-logo.ico"), os.path.join("assets")),
]

a = Analysis(
    [os.path.join(ROOT, "imvu_antibot_installer.py")],
    pathex=[ROOT, os.path.join(ROOT, "src")],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "imvu_toolkit",
        "imvu_toolkit.paths",
        "imvu_toolkit.imvu_process",
        "imvu_toolkit.installer.gui",
        "imvu_toolkit.installer.runner",
        "imvu_toolkit.installer.profiles",
        "imvu_toolkit.zip_utils",
        "imvu_toolkit.patches.antibot.constants",
        "imvu_toolkit.patches.antibot.transforms",
        "imvu_toolkit.patches.antibot.patch",
        "tkinter",
        "_tkinter",
        "PIL",
        "PIL.Image",
        "PIL.ImageTk",
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
    a.binaries,
    a.datas,
    [],
    name="IMVU-Antibot-Installer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON if os.path.exists(ICON) else None,
    version=VERSION_INFO if os.path.exists(VERSION_INFO) else None,
)
