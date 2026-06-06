#!/usr/bin/env python3
"""Backward-compatible wrapper. Prefer: python -m imvu_toolkit dpi dialog-scaling"""

import os
import runpy
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_ROOT, "src"))
os.chdir(_ROOT)
runpy.run_path(os.path.join(_ROOT, "patches", "dpi", "patch_imvu_dialog_scaling.py"), run_name="__main__")
