# Contributing

Thanks for helping improve IMVU Classic Fix Toolkit.

## Getting started

```powershell
git clone https://github.com/JSukar/IMVU-TOOLKIT.git
cd IMVU-TOOLKIT
python -m pip install -e ".[dev]"
pytest
```

## Project layout

| Path | Purpose |
| --- | --- |
| `src/imvu_toolkit/` | Core package (paths, zip helpers, emoji patch) |
| `patches/dpi/` | Optional DPI/layout patch scripts |
| `scripts/` | Probes, emoji catalog generator, scaling helper |
| `emoji_assets/js/` | Injected chat picker and Twemoji scripts |
| `docs/` | Architecture, DPI runbook, compatibility, FAQ |
| `tests/` | Pytest suite (no IMVU install required) |

Root-level `patch_imvu_*.py` files are thin wrappers for backward compatibility.

## Preferred CLI

```powershell
python -m imvu_toolkit emoji install
python -m imvu_toolkit emoji restore
python -m imvu_toolkit emoji generate-list
python -m imvu_toolkit tools scale-window --watch
python -m imvu_toolkit dpi clean-layout --restore
```

## Adding or changing a patch

1. **Use markers** — inject identifiable comment strings so re-runs and restore are safe.
2. **Back up before write** — copy target to `*.bak-<patch>-<timestamp>` before modifying.
3. **Support `--restore`** — restore from the newest matching backup suffix.
4. **Validate before mutate** — fail fast if expected source signatures are missing.
5. **Add tests** — cover transforms with fixtures under `tests/fixtures/` when possible.

## Pull requests

- Keep changes focused; one patch or feature per PR when practical.
- Run `ruff check src tests` and `pytest` before opening a PR.
- Update `CHANGELOG.md` under `[Unreleased]` for user-visible changes.

## Releases

Tag with semver (`v1.0.3`). Pushing a tag triggers the release workflow, which builds `IMVU-Emoji-Installer.zip` on Windows and publishes release notes from `CHANGELOG.md`.

After each release, submit the built `.exe` (inside the zip) to [Microsoft Defender file submission](https://www.microsoft.com/en-us/wdsi/filesubmission) as a false positive (Software developer + link to repo).
