#!/usr/bin/env python3
"""Write PyInstaller Windows version resource for the emoji installer."""

import re
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent.parent
    init_py = root / "src" / "imvu_toolkit" / "__init__.py"
    match = re.search(r'__version__ = "([^"]+)"', init_py.read_text(encoding="utf-8"))
    if not match:
        raise SystemExit("Could not read __version__ from %s" % init_py)
    ver = match.group(1)
    parts = [int(x) for x in ver.split(".")]
    while len(parts) < 4:
        parts.append(0)
    filevers = tuple(parts[:4])
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
        StringStruct(u'FileDescription', u'IMVU Classic Emoji Patch Installer'),
        StringStruct(u'FileVersion', u'{ver_str}'),
        StringStruct(u'InternalName', u'IMVU-Emoji-Installer'),
        StringStruct(u'LegalCopyright', u'MIT License'),
        StringStruct(u'OriginalFilename', u'IMVU-Emoji-Installer.exe'),
        StringStruct(u'ProductName', u'IMVU Toolkit'),
        StringStruct(u'ProductVersion', u'{ver_str}')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
""".format(
        filevers=filevers, ver_str=ver_str
    )

    out = root / "assets" / "installer_version_info.txt"
    out.write_text(content, encoding="utf-8")
    sys.stdout.write("Wrote %s (version %s)\n" % (out, ver))


if __name__ == "__main__":
    main()
