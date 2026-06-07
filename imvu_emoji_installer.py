#!/usr/bin/env python3
"""Windows installer entry point for the IMVU emoji patch."""

import os
import sys

REPO_URL = "https://github.com/JSukar/IMVU-TOOLKIT"


def _setup_path() -> None:
    root = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(root, "src")
    if src not in sys.path:
        sys.path.insert(0, src)


def _cli_main() -> int:
    restore = "--restore" in sys.argv

    from imvu_toolkit import __version__
    from imvu_toolkit.installer.runner import run_patch

    print("=" * 54)
    print("  IMVU Emoji Patch Installer  v%s" % __version__)
    print("  %s" % REPO_URL)
    print("=" * 54)
    if restore:
        print("\nMode: RESTORE (undo emoji patch)")
    else:
        print("\nMode: INSTALL")
        print("If IMVU is open, close it when prompted — the installer waits, then relaunches IMVU.")
    print("")

    code = run_patch(restore=restore)

    print("")
    if code == 0:
        if restore:
            print("Restore complete.")
        else:
            print("Install complete. Click the smiley button beside Send in chat.")
    elif code == 2:
        print("IMVU did not close in time. Close it completely and run this installer again.")
        print("Or use install.ps1 if Windows Defender blocks this .exe.")
    else:
        print("Installer failed. Review the messages above.")

    if os.name == "nt":
        try:
            if sys.stdin is not None and sys.stdin.isatty():
                input("\nPress Enter to exit...")
        except (EOFError, KeyboardInterrupt, OSError):
            pass
    return code


def main() -> int:
    _setup_path()
    if "--cli" in sys.argv:
        return _cli_main()
    from imvu_toolkit.installer.gui import main as gui_main

    return gui_main()


if __name__ == "__main__":
    raise SystemExit(main())
