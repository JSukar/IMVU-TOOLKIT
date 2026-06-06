#!/usr/bin/env python3
"""Backward-compatible wrapper for scripts/fix_imvu_scaling.py"""

import os
import runpy
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_ROOT, "src"))
os.chdir(_ROOT)
runpy.run_path(os.path.join(_ROOT, "scripts", "fix_imvu_scaling.py"), run_name="__main__")
