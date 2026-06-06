#!/usr/bin/env python3
"""Backward-compatible entry point. Prefer: python -m imvu_toolkit emoji install"""

import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from imvu_toolkit.patches.emoji.patch import main

if __name__ == "__main__":
    raise SystemExit(main())
