# Compatibility

Which IMVU Classic setups this toolkit is designed for.

Back to [README](../README.md) | [Architecture](architecture.md) | [FAQ](FAQ.md)

## Platform

| | Supported |
| --- | --- |
| OS | Windows 10 / 11 |
| IMVU variant | IMVU Classic (`IMVUClient.exe` under `%APPDATA%\IMVUClient`) |
| Python (from source) | 3.10+ |
| Installer exe | Windows x64 (bundled Python) |

## Emoji patch

| Feature | Status | Notes |
| --- | --- | --- |
| Chat Twemoji rendering | ✅ Verified on maintainer build | Requires restart after patch |
| Emoji picker + search | ✅ | ~1,880 Unicode 15.1 emojis |
| Text shortcuts | ✅ | Replace or append mode |
| Offline emoji (cached) | ⚠️ Partial | First load needs jsDelivr |
| Profile / room title emoji | ❌ | Chat only |
| IMVU update overwrites patch | ⚠️ | Re-run installer after client update |

**If patch fails with signature errors:** your `library.zip` layout may differ. Open a [bug report](https://github.com/JSukar/IMVU-TOOLKIT/issues/new?template=bug_report.yml) and note whether `im/common.pyo` exists.

## DPI patches

| Patch | Depends on | Risk |
| --- | --- | --- |
| `fix_imvu_scaling.py` | None | Low — registry + window resize only |
| `patch_imvu_clean_dpi_layout.py` | None (start here for sharp mode) | Medium |
| `patch_imvu_room_overlay_hitboxes.py` | clean-layout marker | Medium |
| `patch_imvu_overlay_click_remap.py` | None | Medium |
| `patch_imvu_dialog_scaling.py` | None | Medium |
| `patch_imvu_white_line.py` | None | Low |

Try **Windows-level scaling first** ([dpi-patches.md](dpi-patches.md#first-to-try-windows-level-scaling-fix)) before internal patches.

## Reporting compatibility

When opening an issue, include:

- Windows version and display scale (e.g. 250% / 240 DPI)
- IMVU Classic version or build date (if known)
- Toolkit version (`python -m imvu_toolkit --version` or installer banner)
- Whether `im/common.pyo` or only `im/common.py` exists in your `library.zip`

We maintain this table as users confirm builds — [open an issue](https://github.com/JSukar/IMVU-TOOLKIT/issues) to add yours.
