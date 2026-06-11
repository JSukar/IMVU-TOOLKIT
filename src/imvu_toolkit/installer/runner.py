"""Shared install/restore runner for CLI and GUI installers."""

from __future__ import annotations

import os
import sys


def ensure_import_path(root: str | None = None) -> str:
    root = root or os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(root, "..", "..", ".."))
    src = os.path.join(repo_root, "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    return repo_root


def run_patch(restore: bool = False, patch: str = "emoji") -> int:
    if patch == "antibot":
        from imvu_toolkit.patches.antibot.patch import main as patch_main
    elif patch == "emoji":
        from imvu_toolkit.patches.emoji.patch import main as patch_main
    else:
        raise ValueError("Unknown patch type: %s" % patch)

    argv = ["--relaunch-imvu"]
    if restore:
        argv.append("--restore")
    return patch_main(argv)
