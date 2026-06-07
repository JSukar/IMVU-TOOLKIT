# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-06-07

### Added

- Emoji picker **Favorites** — ★ header button; click ☆ on an emoji to add or remove

### Fixed

- **Transparent app icon** — regenerate `.ico` from the PNG with proper alpha (`scripts/generate_icon.py`); exe/window icons no longer show a solid background

## [1.0.4] - 2026-06-03

### Added

- Emoji picker **Favorites** — ★ header button; click ☆ on an emoji to add or remove
- **`--relaunch-imvu`** — start IMVU after a successful emoji install or restore
- **GUI installer** — tkinter window with Install / Restore buttons and live log (`IMVU-Emoji-Installer.exe`, `install_gui.ps1`)

### Changed

- Release asset is a standalone **`IMVU-Emoji-Installer.exe`** (onefile GUI) instead of a zip folder
- `install.ps1` and the `.exe` installer prompt you to close IMVU, wait until it exits, patch, then relaunch (no force-kill)
- Emoji favorites: click ☆ on an emoji to toggle; header ★ opens favorites view

## [1.0.3] - 2026-06-03

### Added

- `install.ps1` — install/restore via Python (recommended when Windows Defender blocks the `.exe`)
- Windows version metadata on the installer (`scripts/generate_version_info.py`)

### Changed

- Installer ships as **onedir** folder inside `IMVU-Emoji-Installer.zip` (fewer Defender false positives than onefile)
- Installer no longer force-kills IMVU (`taskkill /F` removed); close IMVU manually or use graceful window close
- Release asset is `IMVU-Emoji-Installer.zip` (run `IMVU-Emoji-Installer.exe` inside the extracted folder)

### Fixed

- Reduced antivirus false positives: disabled UPX, removed aggressive process termination, added file version info

## [1.0.2] - 2026-06-03

### Added

- CI status badge, SmartScreen / FAQ docs, split documentation (`docs/architecture.md`, `docs/dpi-patches.md`, `docs/compatibility.md`, `docs/FAQ.md`)
- Jar patch integration test (apply + restore round-trip)
- Dependabot for GitHub Actions and pip
- CLI: `emoji generate-list`, `tools scale-window|dpi-probe|…`
- DPI patch registry (`imvu_toolkit.patches.dpi`) and tools runner
- Release notes extracted from CHANGELOG on tag push
- Enhanced bug report template (IMVU path, toolkit version, diagnostics)

### Fixed

- Jar rewrite injects new `js/emoji*.js` files when absent from the source jar

### Changed

- README trimmed; DPI content moved to `docs/dpi-patches.md`
- Installer banner shows version (`v1.0.2`)
- Expanded `.gitignore` for pytest/ruff/egg-info caches

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

[1.1.0]: https://github.com/JSukar/IMVU-TOOLKIT/releases/tag/v1.1.0
[1.0.4]: https://github.com/JSukar/IMVU-TOOLKIT/releases/tag/v1.0.4
[1.0.3]: https://github.com/JSukar/IMVU-TOOLKIT/releases/tag/v1.0.3
[1.0.2]: https://github.com/JSukar/IMVU-TOOLKIT/releases/tag/v1.0.2
[1.0.1]: https://github.com/JSukar/IMVU-TOOLKIT/releases/tag/v1.0.1
[1.0.0]: https://github.com/JSukar/IMVU-TOOLKIT/releases/tag/v1.0.0
