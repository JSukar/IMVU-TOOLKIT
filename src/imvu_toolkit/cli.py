"""Unified CLI for IMVU Classic Fix Toolkit."""

import argparse
import os
import runpy
import sys

from imvu_toolkit import __version__
from imvu_toolkit.patches.emoji.patch import main as emoji_main
from imvu_toolkit.paths import project_root

DPI_SCRIPTS = {
    "clean-layout": "patch_imvu_clean_dpi_layout.py",
    "dialog-scaling": "patch_imvu_dialog_scaling.py",
    "overlay-click": "patch_imvu_overlay_click_remap.py",
    "room-hitboxes": "patch_imvu_room_overlay_hitboxes.py",
    "white-line": "patch_imvu_white_line.py",
}


def run_dpi_patch(name, argv):
    script_name = DPI_SCRIPTS.get(name)
    if not script_name:
        raise SystemExit("Unknown DPI patch: %s" % name)
    script_path = os.path.join(project_root(), "patches", "dpi", script_name)
    if not os.path.isfile(script_path):
        raise SystemExit("Patch script not found: %s" % script_path)
    saved_argv = sys.argv
    try:
        sys.argv = [script_path] + list(argv)
        runpy.run_path(script_path, run_name="__main__")
    finally:
        sys.argv = saved_argv
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="imvu-toolkit",
        description="IMVU Classic Fix Toolkit — emoji rendering and optional DPI patches.",
    )
    parser.add_argument("--version", action="version", version="%(prog)s " + __version__)
    sub = parser.add_subparsers(dest="command", required=True)

    emoji = sub.add_parser("emoji", help="Emoji picker and Twemoji chat rendering patch")
    emoji_sub = emoji.add_subparsers(dest="emoji_action", required=True)

    emoji_install = emoji_sub.add_parser("install", help="Install the emoji patch")
    emoji_install.add_argument("--imvu-dir", default=None)
    emoji_install.add_argument("--library")
    emoji_install.add_argument("--content-jar")
    emoji_install.add_argument("--force", action="store_true")
    emoji_install.add_argument("--no-close-imvu", action="store_true")

    emoji_restore = emoji_sub.add_parser("restore", help="Restore emoji patch backups")
    emoji_restore.add_argument("--imvu-dir", default=None)
    emoji_restore.add_argument("--library")
    emoji_restore.add_argument("--content-jar")
    emoji_restore.add_argument("--force", action="store_true")
    emoji_restore.add_argument("--no-close-imvu", action="store_true")

    dpi = sub.add_parser("dpi", help="DPI and layout patches (advanced)")
    dpi_sub = dpi.add_subparsers(dest="dpi_patch", required=True)
    for patch_name in DPI_SCRIPTS:
        p = dpi_sub.add_parser(
            patch_name, help="Run %s patch (passes through script flags)" % patch_name
        )
        p.add_argument("extra", nargs=argparse.REMAINDER, help=argparse.SUPPRESS)

    return parser


def emoji_args_from_namespace(ns, restore=False):
    argv = []
    if restore:
        argv.append("--restore")
    if ns.imvu_dir:
        argv.extend(["--imvu-dir", ns.imvu_dir])
    if getattr(ns, "library", None):
        argv.extend(["--library", ns.library])
    if getattr(ns, "content_jar", None):
        argv.extend(["--content-jar", ns.content_jar])
    if getattr(ns, "force", False):
        argv.append("--force")
    if getattr(ns, "no_close_imvu", False):
        argv.append("--no-close-imvu")
    return argv


def main(argv=None):
    parser = build_parser()
    ns = parser.parse_args(argv)

    if ns.command == "emoji":
        return emoji_main(emoji_args_from_namespace(ns, restore=(ns.emoji_action == "restore")))

    if ns.command == "dpi":
        extra = list(getattr(ns, "extra", []) or [])
        if extra and extra[0] == "--":
            extra = extra[1:]
        return run_dpi_patch(ns.dpi_patch, extra)

    parser.error("Unknown command")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
