# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.1] - 2026-06-11

### Added

- **Forged JSON `chatId` detection** — boots third-party injectors that hardcode `"chatId": "141"` while the IMQ queue is the real room id (Findzu/Findgu-style prejoin protocol); boot reason `forged_chat_id`
- **Findzu / Findgu promo markers** — `findzu.net`, `findgu.net` in normalized message text (fallback when chat id is correct)
- **`tools/analyze_chatid_mismatch.py`** — scans `IMVULog.log*` for JSON `chatId` vs queue mismatches (used to validate zero false positives on normal users before shipping)

### Changed

- `check_incoming_message()` evaluates forged chat id **before** promo text so prejoin `*isPureUser` / `*putOnOutfit` bursts are booted immediately
- **`docs/antibot.md`** — Pattern C (Findzu), forged-chat-id rules, chatId log analysis notes

## [1.2.0] - 2026-06-03

### Added

- **Room antibot patch** — room owners and mods auto-boot VuArchives promo bots when spam messages match known patterns (`vuarchives.com`, tracking IDs, etc.)
- **Shield UI** in chat — green shield when active; popup with **Boot log** and **Whitelist** tabs
- **Whitelist** — add/remove trusted users; paginated list; persisted to `%APPDATA%\IMVUClient\antibot_whitelist.json` (built-in trusted IDs included)
- CLI: `python -m imvu_toolkit antibot install|restore`
- **`IMVU-Antibot-Installer.exe`** GUI installer (Install / Restore, live log) plus `install_antibot.ps1` and `install_antibot_gui.ps1`
- Restore from `.bak-antibot-*` backups on `library.zip` and `imvuContent.jar`
- CI and release workflow publish **both** `IMVU-Emoji-Installer.exe` and `IMVU-Antibot-Installer.exe`
- **`docs/antibot.md`** — install guide, detection rules, architecture, bot research, and screenshots

### Fixed

- Antibot popup no longer turns the chat panel black (popup appended to `document.body` with fixed positioning)
- Whitelist tab no longer overflows the popup; fixed height, scrollable body, and pagination
- GUI installer `profile=` keyword crash (`profile_id=` in antibot and emoji entry points)
- `imvu.call.apply` crash on IMVU’s old Gecko engine (direct `imvu.call` in antibot JS)
- Decompiled Python patches cleaned before inject (`_clean_decompiled_source`) to avoid IMVU crashes

### Changed

- Shared installer framework (`installer/profiles.py`) parameterized for emoji and antibot builds
- `build_installer.ps1` builds both installer executables
- README and `docs/architecture.md` link to antibot documentation

## [1.1.1] - 2026-06-08

### Fixed

- Empty **Favorites** tab no longer stacks the hint lines on top of each other (grid `line-height: 0` override)
- GUI installer taskbar icon uses HiDPI `.ico` sizes (20–256px) and Win32 `WM_SETICON` for a sharper taskbar icon
- GUI install no longer flashes PowerShell windows while waiting for IMVU to close; duplicate install clicks are ignored
- GUI install wait loop no longer crashes when stdout is redirected to the log panel

### Changed

- **Tab** accepts text shortcut suggestions (replace or append per gear setting); improved handling on IMVU's Gecko engine
- Expanded text shortcut dictionary (300+ words: slang, food, gaming, emoticons, reactions)
- README includes GUI installer screenshot

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

[1.2.1]: https://github.com/JSukar/IMVU-TOOLKIT/releases/tag/v1.2.1
[1.2.0]: https://github.com/JSukar/IMVU-TOOLKIT/releases/tag/v1.2.0
[1.1.1]: https://github.com/JSukar/IMVU-TOOLKIT/releases/tag/v1.1.1
[1.1.0]: https://github.com/JSukar/IMVU-TOOLKIT/releases/tag/v1.1.0
[1.0.4]: https://github.com/JSukar/IMVU-TOOLKIT/releases/tag/v1.0.4
[1.0.3]: https://github.com/JSukar/IMVU-TOOLKIT/releases/tag/v1.0.3
[1.0.2]: https://github.com/JSukar/IMVU-TOOLKIT/releases/tag/v1.0.2
[1.0.1]: https://github.com/JSukar/IMVU-TOOLKIT/releases/tag/v1.0.1
[1.0.0]: https://github.com/JSukar/IMVU-TOOLKIT/releases/tag/v1.0.0
