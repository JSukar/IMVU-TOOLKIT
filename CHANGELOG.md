# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-06-03

### Added

- `src/imvu_toolkit/` package with split emoji patch modules
- Unified CLI: `python -m imvu_toolkit emoji install|restore` and `dpi` subcommands
- Pytest suite, GitHub Actions CI, and tag-triggered release workflow
- `CONTRIBUTING.md`, `SECURITY.md`, issue templates, pre-commit + Ruff

### Changed

- DPI patches moved to `patches/dpi/`; utilities to `scripts/` (root wrappers unchanged)
- Stop tracking `__pycache__` in git

## [1.0.0] - 2026-06-03

### Added

- Searchable emoji picker with ~1,880 Unicode 15.1 emojis next to **Send**
- Twemoji rendering for IMVU Classic chat (Gecko engine)
- Text shortcuts (e.g. `lol` → 😂) with replace/append modes
- Gear settings and about panel in picker header
- `IMVU-Emoji-Installer.exe` Windows installer (PyInstaller bundle)
- Auto-close IMVU before patching (overridable with `--no-close-imvu`)
- Unified CLI: `python -m imvu_toolkit emoji install|restore` and `dpi` subcommands
- Pytest coverage for emoji transform and zip patch logic
- GitHub Actions CI (tests + Windows release build on tag)
- Pre-commit hooks with Ruff

### Changed

- Refactored emoji patch into `src/imvu_toolkit/` package
- Moved DPI patch scripts to `patches/dpi/` (root wrappers preserved)
- Moved utility scripts to `scripts/` (root wrappers preserved)

[1.0.1]: https://github.com/JSukar/IMVU-TOOLKIT/releases/tag/v1.0.1
[1.0.0]: https://github.com/JSukar/IMVU-TOOLKIT/releases/tag/v1.0.0
