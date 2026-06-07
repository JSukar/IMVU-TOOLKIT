import subprocess
import sys
from pathlib import Path

from imvu_toolkit import __version__


def test_extract_changelog_for_current_version():
    root = Path(__file__).resolve().parents[1]
    script = root / "scripts" / "extract_changelog.py"
    result = subprocess.run(
        [sys.executable, str(script), str(root / "CHANGELOG.md"), "v" + __version__],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "### Added" in result.stdout or "### Changed" in result.stdout
    assert "Unreleased" not in result.stdout
