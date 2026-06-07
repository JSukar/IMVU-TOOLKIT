#!/usr/bin/env python3
"""Windows installer entry point for the IMVU emoji patch."""

import os
import sys

REPO_URL = "https://github.com/JSukar/IMVU-TOOLKIT"


def pause_if_needed():
    if os.name != "nt":
        return
    try:
        if sys.stdin is None or not sys.stdin.isatty():
            input("\nPress Enter to exit...")
    except (EOFError, KeyboardInterrupt, OSError):
        pass


def print_banner(restore):
    from imvu_toolkit import __version__

    print("=" * 54)
    print("  IMVU Emoji Patch Installer  v%s" % __version__)
    print("  %s" % REPO_URL)
    print("=" * 54)
    if restore:
        print("\nMode: RESTORE (undo emoji patch)")
    else:
        print("\nMode: INSTALL")
        print("Close IMVU before continuing (this build does not force-kill IMVU).")
    print("")


def main():
    restore = "--restore" in sys.argv

    root = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(root, "src")
    if src not in sys.path:
        sys.path.insert(0, src)

    print_banner(restore)

    from imvu_toolkit.patches.emoji.patch import main as patch_main

    argv = ["--no-close-imvu"]
    if restore:
        argv.append("--restore")

    code = patch_main(argv)

    print("")
    if code == 0:
        if restore:
            print("Restore complete. Restart IMVU.")
        else:
            print("Install complete. Restart IMVU and click the smiley button beside Send.")
    elif code == 2:
        print("Close IMVU manually and run this installer again.")
        print("Or use install.ps1 if Windows Defender blocks this .exe.")
    else:
        print("Installer failed. Review the messages above.")

    pause_if_needed()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
