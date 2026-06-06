#!/usr/bin/env python3
"""Backward-compatible wrapper for scripts/compare_imvu_probes.py"""

import os
import runpy
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_ROOT, "src"))
os.chdir(_ROOT)
runpy.run_path(os.path.join(_ROOT, "scripts", "compare_imvu_probes.py"), run_name="__main__")
