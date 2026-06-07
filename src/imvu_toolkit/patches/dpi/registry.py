"""Registry and launcher for DPI patch scripts."""

import os
import runpy
import sys

from imvu_toolkit.paths import project_root

DPI_SCRIPTS = {
    "clean-layout": "patch_imvu_clean_dpi_layout.py",
    "dialog-scaling": "patch_imvu_dialog_scaling.py",
    "overlay-click": "patch_imvu_overlay_click_remap.py",
    "room-hitboxes": "patch_imvu_room_overlay_hitboxes.py",
    "white-line": "patch_imvu_white_line.py",
}


def dpi_script_path(name):
    script_name = DPI_SCRIPTS.get(name)
    if not script_name:
        return None
    return os.path.join(project_root(), "patches", "dpi", script_name)


def run_dpi_patch(name, argv):
    script_path = dpi_script_path(name)
    if not script_path or not os.path.isfile(script_path):
        raise SystemExit("Patch script not found for: %s" % name)
    saved_argv = sys.argv
    try:
        sys.argv = [script_path] + list(argv)
        runpy.run_path(script_path, run_name="__main__")
    finally:
        sys.argv = saved_argv
    return 0
