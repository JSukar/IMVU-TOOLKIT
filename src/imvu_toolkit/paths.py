import os
import sys


def project_root():
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def asset_path(*parts):
    return os.path.join(project_root(), *parts)


DEFAULT_IMVU_DIR = os.path.join(os.environ.get("APPDATA", ""), "IMVUClient")
