# FAQ

Back to [README](../README.md) | [Architecture](architecture.md) | [Compatibility](compatibility.md)

## Installer & Windows

### Windows says "Unknown publisher"

The installer is not code-signed. Click **More info** → **Run anyway**. Download only from [official Releases](https://github.com/JSukar/IMVU-TOOLKIT/releases).

### Windows Defender blocks or deletes the installer

Defender is **stronger than SmartScreen** — it may quarantine the `.exe` before you can run it. That is a known false positive for unsigned PyInstaller patch tools (same build as [GitHub Actions](https://github.com/JSukar/IMVU-TOOLKIT/actions); see source on GitHub).

**Fastest workaround — run `install.ps1`** (same patch, no PyInstaller `.exe`):

```powershell
git clone https://github.com/JSukar/IMVU-TOOLKIT.git
cd IMVU-TOOLKIT
.\install.ps1
```

The installer asks you to close IMVU if it is running, waits until it exits, applies the patch, then relaunches IMVU. Restore: `.\install.ps1 --restore`

Requires Python 3.10+. If you already cloned the repo locally, run `.\install.ps1` from the project folder.

If you already downloaded the installer and want to run it anyway:

1. **Protection history** — *Settings* → *Privacy & security* → *Windows Security* → *Virus & threat protection* → *Protection history* → select `IMVU-Emoji-Installer.exe` → **Restore** → **Allow on device** (wording may vary).
2. **Unblock download** (SmartScreen / Mark of the Web) — PowerShell in the download folder:
   ```powershell
   Unblock-File -LiteralPath .\IMVU-Emoji-Installer.exe
   ```
3. **Exclusion (your PC only)** — *Virus & threat protection* → *Manage settings* → *Exclusions* → *Add an exclusion* → *File* → pick the `.exe`. Only do this if you verified SHA256 from [Releases](https://github.com/JSukar/IMVU-TOOLKIT/releases/latest).

**Maintainer:** after each release, submit the `.exe` as a false positive to [Microsoft Defender submissions](https://www.microsoft.com/en-us/wdsi/filesubmission) (pick *Software developer*, link to the repo/release). That can clear Defender for everyone over time — code signing is still the best long-term fix.

### Is the installer safe? (VirusTotal)

The `.exe` is built from this repo by [GitHub Actions](https://github.com/JSukar/IMVU-TOOLKIT/actions) — no bundled adware or installers.

1. Download only from [Releases](https://github.com/JSukar/IMVU-TOOLKIT/releases/latest).
2. Confirm the **SHA256** on the release asset matches your file (PowerShell: `Get-FileHash .\\IMVU-Emoji-Installer.exe -Algorithm SHA256`).
3. See the linked **[VirusTotal report](https://www.virustotal.com/gui/file/298fa3563585a13f67eeaccb6ac7b4c092e2e43c1a35250e14b519bf12436a48)** for the current v1.0.2 build (hash-based; updates each release).

If VirusTotal shows “file not found,” the maintainer may not have submitted that build yet — use the SHA256 check and inspect the source here on GitHub.

### VirusTotal shows a few detections (e.g. 5/71) — is it malware?

**Almost certainly false positives**, not proof of malware. For unsigned PyInstaller `.exe` files, a handful of heuristic hits is normal; **most engines (60+) reporting “clean” is what you want to look at.**

Common reasons AV heuristics flag this installer:

| Behavior | Why scanners care | What we actually do |
| --- | --- | --- |
| Self-extracting single `.exe` | Same packer pattern as some trojans | PyInstaller bundles Python + your patch code |
| Not code-signed | No publisher reputation | Same as SmartScreen “Unknown publisher” |
| Closes another process | “Hacktool” / “PUA” heuristics | User closes IMVU manually; installer waits (no force-kill) |
| Edits files under `%APPDATA%` | Generic “modifier” behavior | Patches `library.zip` / `imvuContent.jar` only |

**How to verify yourself:** read the [source](https://github.com/JSukar/IMVU-TOOLKIT), match SHA256 to the release, and compare detections before/after each release. Microsoft Defender and other major vendors usually show **undetected** when the build is clean.

**What helps long term:** code signing (best fix), rebuilding without UPX compression (done in `imvu_emoji_installer.spec` from v1.0.3+), and submitting a **false-positive report** on the VirusTotal page (**Contact vendor** / vendor-specific forms) after each new release.

Names like *HackTool*, *PUA*, *Generic.ml*, or *PyInstaller* in a detection label are typical for open-source patch tools, not confirmed malware.

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

### Do favorites persist after I restart IMVU?

**Yes, on the same PC** — favorites are saved in the browser’s `localStorage` (same storage the emoji image cache uses). They should survive closing and reopening IMVU, and rebooting Windows.

If favorites disappear after a restart, IMVU’s embedded browser may have cleared storage for that profile; re-add them with ☆. Favorites are not synced to other computers or IMVU accounts.

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
