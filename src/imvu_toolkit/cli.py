"""Unified CLI for IMVU Classic Fix Toolkit."""

import argparse

from imvu_toolkit import __version__
from imvu_toolkit.patches.antibot.patch import main as antibot_main
from imvu_toolkit.patches.dpi.registry import DPI_SCRIPTS, run_dpi_patch
from imvu_toolkit.patches.emoji.patch import main as emoji_main
from imvu_toolkit.tools.runner import TOOL_SCRIPTS, run_tool


def build_parser():
    parser = argparse.ArgumentParser(
        prog="imvu-toolkit",
        description=(
            "IMVU Classic Fix Toolkit — emoji rendering, room antibot, "
            "and optional DPI patches."
        ),
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
    emoji_install.add_argument("--relaunch-imvu", action="store_true")

    emoji_restore = emoji_sub.add_parser("restore", help="Restore emoji patch backups")
    emoji_restore.add_argument("--imvu-dir", default=None)
    emoji_restore.add_argument("--library")
    emoji_restore.add_argument("--content-jar")
    emoji_restore.add_argument("--force", action="store_true")
    emoji_restore.add_argument("--no-close-imvu", action="store_true")
    emoji_restore.add_argument("--relaunch-imvu", action="store_true")

    emoji_gen = emoji_sub.add_parser(
        "generate-list", help="Regenerate emojiList.js from Unicode emoji-test.txt"
    )
    emoji_gen.add_argument("extra", nargs=argparse.REMAINDER, help=argparse.SUPPRESS)

    antibot = sub.add_parser(
        "antibot",
        help="Auto-boot VuArchives-style promo bots in rooms you own or mod",
    )
    antibot_sub = antibot.add_subparsers(dest="antibot_action", required=True)

    antibot_install = antibot_sub.add_parser("install", help="Install the room antibot patch")
    antibot_install.add_argument("--imvu-dir", default=None)
    antibot_install.add_argument("--library")
    antibot_install.add_argument("--content-jar")
    antibot_install.add_argument("--force", action="store_true")
    antibot_install.add_argument("--no-close-imvu", action="store_true")
    antibot_install.add_argument("--relaunch-imvu", action="store_true")

    antibot_restore = antibot_sub.add_parser("restore", help="Restore antibot patch backups")
    antibot_restore.add_argument("--imvu-dir", default=None)
    antibot_restore.add_argument("--library")
    antibot_restore.add_argument("--content-jar")
    antibot_restore.add_argument("--force", action="store_true")
    antibot_restore.add_argument("--no-close-imvu", action="store_true")
    antibot_restore.add_argument("--relaunch-imvu", action="store_true")

    dpi = sub.add_parser("dpi", help="DPI and layout patches (advanced)")
    dpi_sub = dpi.add_subparsers(dest="dpi_patch", required=True)
    for patch_name in DPI_SCRIPTS:
        help_text = "Run %s patch (passes through script flags)" % patch_name
        p = dpi_sub.add_parser(patch_name, help=help_text)
        p.add_argument("extra", nargs=argparse.REMAINDER, help=argparse.SUPPRESS)

    tools = sub.add_parser("tools", help="Utility scripts (scaling, probes, catalog)")
    tools_sub = tools.add_subparsers(dest="tool", required=True)
    for tool_name in TOOL_SCRIPTS:
        help_text = "Run %s (passes through script flags)" % tool_name
        p = tools_sub.add_parser(tool_name, help=help_text)
        p.add_argument("extra", nargs=argparse.REMAINDER, help=argparse.SUPPRESS)

    return parser


def antibot_args_from_namespace(ns, restore=False):
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
    if getattr(ns, "relaunch_imvu", False):
        argv.append("--relaunch-imvu")
    return argv


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
    if getattr(ns, "relaunch_imvu", False):
        argv.append("--relaunch-imvu")
    return argv


def _remainder(ns):
    extra = list(getattr(ns, "extra", []) or [])
    if extra and extra[0] == "--":
        extra = extra[1:]
    return extra


def main(argv=None):
    parser = build_parser()
    ns = parser.parse_args(argv)

    if ns.command == "emoji":
        if ns.emoji_action == "generate-list":
            return run_tool("generate-emoji-list", _remainder(ns))
        return emoji_main(emoji_args_from_namespace(ns, restore=(ns.emoji_action == "restore")))

    if ns.command == "antibot":
        return antibot_main(
            antibot_args_from_namespace(ns, restore=(ns.antibot_action == "restore"))
        )

    if ns.command == "dpi":
        return run_dpi_patch(ns.dpi_patch, _remainder(ns))

    if ns.command == "tools":
        return run_tool(ns.tool, _remainder(ns))

    parser.error("Unknown command")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
