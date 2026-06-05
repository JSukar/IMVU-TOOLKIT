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
    print("=" * 54)
    print("  IMVU Emoji Patch Installer")
    print("  %s" % REPO_URL)
    print("=" * 54)
    if restore:
        print("\nMode: RESTORE (undo emoji patch)")
    else:
        print("\nMode: INSTALL")
        print("If IMVU is open, this installer will close it automatically.")
    print("")


def main():
    restore = "--restore" in sys.argv
    print_banner(restore)

    from patch_imvu_emoji import main as patch_main

    code = patch_main()

    print("")
    if code == 0:
        if restore:
            print("Restore complete. Restart IMVU.")
        else:
            print("Install complete. Restart IMVU and click the smiley button beside Send.")
    elif code == 2:
        print("Could not close IMVU. Close it manually and run this installer again.")
    else:
        print("Installer failed. Review the messages above.")

    pause_if_needed()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
