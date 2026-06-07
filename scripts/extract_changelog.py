#!/usr/bin/env python3
"""Extract a version section from CHANGELOG.md for GitHub Releases."""

import re
import sys
from pathlib import Path


def extract_version_section(changelog_text, version):
    version = version.lstrip("v")
    pattern = rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)"
    match = re.search(pattern, changelog_text, flags=re.MULTILINE | re.DOTALL)
    if not match:
        raise SystemExit("No changelog section found for version %s" % version)
    return match.group(1).strip() + "\n"


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: extract_changelog.py <changelog.md> <version>")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    changelog_path = Path(sys.argv[1])
    version = sys.argv[2]
    text = changelog_path.read_text(encoding="utf-8")
    sys.stdout.write(extract_version_section(text, version))


if __name__ == "__main__":
    main()
