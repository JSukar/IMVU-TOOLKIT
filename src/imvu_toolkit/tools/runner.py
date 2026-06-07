"""Run utility scripts from the scripts/ directory."""

import os
import runpy
import sys

from imvu_toolkit.paths import project_root

TOOL_SCRIPTS = {
    "scale-window": "fix_imvu_scaling.py",
    "dpi-probe": "imvu_dpi_runtime_probe.py",
    "audit-probe": "audit_imvu_dpi_probe.py",
    "compare-probes": "compare_imvu_probes.py",
    "generate-emoji-list": "generate_emoji_list.py",
}


def tool_script_path(name):
    script_name = TOOL_SCRIPTS.get(name)
    if not script_name:
        return None
    return os.path.join(project_root(), "scripts", script_name)


def run_tool(name, argv):
    script_path = tool_script_path(name)
    if not script_path or not os.path.isfile(script_path):
        raise SystemExit("Tool script not found for: %s" % name)
    root = project_root()
    saved_argv = sys.argv
    saved_cwd = os.getcwd()
    try:
        os.chdir(root)
        sys.argv = [script_path] + list(argv)
        runpy.run_path(script_path, run_name="__main__")
    finally:
        sys.argv = saved_argv
        os.chdir(saved_cwd)
    return 0
