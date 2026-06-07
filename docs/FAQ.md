# FAQ

Back to [README](../README.md) | [Architecture](architecture.md) | [Compatibility](compatibility.md)

## Installer & Windows

### Windows says "Unknown publisher"

The installer is not code-signed. Click **More info** → **Run anyway**. Download only from [official Releases](https://github.com/JSukar/IMVU-TOOLKIT/releases).

### IMVU was open when I ran the installer

The installer tries to close IMVU automatically. If that fails, close IMVU manually and run again.

### How do I undo the emoji patch?

```powershell
IMVU-Emoji-Installer.exe --restore
# or
python patch_imvu_emoji.py --restore
python -m imvu_toolkit emoji restore
```

## Emoji

### Picker button missing

Restart IMVU after patching. If you had an older emoji-only install, re-run the patch to upgrade injected JS.

### Emoji show as hex boxes (tofu)

Patch did not apply or IMVU was not restarted. Close IMVU, run the patch, reopen.

### Emoji images broken in chat

Allow `cdn.jsdelivr.net` (and optionally `emojicdn.elk.sh`) through firewall/VPN. First session needs internet; later loads use localStorage cache.

### Picker clipped or hidden

The picker uses a parent-window overlay when allowed. Some room layouts may still clip — report with a screenshot.

### Shortcuts not working / wrong mode

Open the gear icon → choose **Replace** vs **Keep word, add emoji after**, and **Show** vs **Hide** suggestions. Re-run patch if JS was outdated.

## DPI

### Should I use DPI patches or emoji only?

Emoji patch is independent. Use [fix_imvu_scaling.py](../fix_imvu_scaling.py) first for DPI issues; see [dpi-patches.md](dpi-patches.md).

### IMVU broke after an update

Client updates can overwrite `library.zip` / `imvuContent.jar`. Restore old backups if needed, then re-apply patches.

## Development

### Where are backups?

Next to the patched files, e.g. `library.zip.bak-emoji-*`, `imvuContent.jar.bak-emoji-*`.

### How do I run tests?

```powershell
python -m pip install -e ".[dev]"
pytest
```

## Community

Questions and show-and-tell: enable [GitHub Discussions](https://github.com/JSukar/IMVU-TOOLKIT/discussions) on the repo (Settings → General → Features) and use the **Q&A** category.

Bug reports: use the [bug report template](https://github.com/JSukar/IMVU-TOOLKIT/issues/new?template=bug_report.yml).
