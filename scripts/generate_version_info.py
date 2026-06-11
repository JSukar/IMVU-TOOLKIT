#!/usr/bin/env python3
"""Write PyInstaller Windows version resources for installer .exe builds."""

import re
import sys
from pathlib import Path

INSTALLERS = (
    {
        "filename": "installer_version_info.txt",
        "description": "IMVU Classic Emoji Patch Installer",
        "internal_name": "IMVU-Emoji-Installer",
        "original_filename": "IMVU-Emoji-Installer.exe",
    },
    {
        "filename": "antibot_installer_version_info.txt",
        "description": "IMVU Classic Antibot Patch Installer",
        "internal_name": "IMVU-Antibot-Installer",
        "original_filename": "IMVU-Antibot-Installer.exe",
    },
)


def version_tuple(init_py: Path) -> tuple[int, ...]:
    match = re.search(r'__version__ = "([^"]+)"', init_py.read_text(encoding="utf-8"))
    if not match:
        raise SystemExit("Could not read __version__ from %s" % init_py)
    parts = [int(x) for x in match.group(1).split(".")]
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts[:4])


def write_version_info(out: Path, meta: dict, filevers: tuple[int, ...]) -> None:
    ver_str = ".".join(str(p) for p in filevers)
    content = """# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={filevers},
    prodvers={filevers},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'JSukar'),
        StringStruct(u'FileDescription', u'{description}'),
        StringStruct(u'FileVersion', u'{ver_str}'),
        StringStruct(u'InternalName', u'{internal_name}'),
        StringStruct(u'LegalCopyright', u'MIT License'),
        StringStruct(u'OriginalFilename', u'{original_filename}'),
        StringStruct(u'ProductName', u'IMVU Toolkit'),
        StringStruct(u'ProductVersion', u'{ver_str}')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
""".format(
        filevers=filevers,
        ver_str=ver_str,
        description=meta["description"],
        internal_name=meta["internal_name"],
        original_filename=meta["original_filename"],
    )
    out.write_text(content, encoding="utf-8")
    sys.stdout.write("Wrote %s (version %s)\n" % (out, ver_str))


def main():
    root = Path(__file__).resolve().parent.parent
    init_py = root / "src" / "imvu_toolkit" / "__init__.py"
    filevers = version_tuple(init_py)
    assets = root / "assets"
    for meta in INSTALLERS:
        write_version_info(assets / meta["filename"], meta, filevers)


if __name__ == "__main__":
    main()
