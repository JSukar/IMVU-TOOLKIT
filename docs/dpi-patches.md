# Sharp-DPI Fix (High-DPI Displays)

Technical tooling for diagnosing and patching IMVU Classic DPI-scaling regressions on high-DPI displays.

Back to [README](../README.md) | [Architecture](architecture.md) | [Compatibility](compatibility.md) | [FAQ](FAQ.md)
## Sharp-DPI Fix (High-DPI Displays)

Technical tooling for diagnosing and patching IMVU Classic DPI-scaling regressions on high-DPI displays (for example, 240 DPI / 250% scale).

This includes a safe **Windows compatibility scaling helper** plus optional **mechanical, reversible binary/source patching** of IMVU runtime assets (`library.zip` and `imvuContent.jar`) and **window-level instrumentation** to validate behavior before/after each patch.

> **Note:** This does not fully fix in-room UI behavior or notification issues yet. I did not finish those parts, so feel free to modify and extend this project to make it fully functional (I got lazy).

---

### First to Try: Windows-Level Scaling Fix

Start with `fix_imvu_scaling.py` before using the internal patch scripts.

This is the clean, safe compatibility fix. It does **not** patch IMVU's
`library.zip`, `imvuContent.jar`, CSS, Gecko overlays, dialogs, room code,
`_avatarwindow.pyd`, `SceneWindow.dll`, or any other IMVU client file. Instead,
it asks Windows to run and size the IMVU window in a DPI mode that keeps the
whole client in one coordinate system.

Default command:

```powershell
python .\fix_imvu_scaling.py
```

Recommended persistent/watch mode while testing:

```powershell
python .\fix_imvu_scaling.py --watch
```

What the default `lowres` preset does:

- Finds visible top-level `IMVUClient.exe` windows.
- Sets IMVU's registry DPI preference to `Recommended`:
  - `HKCU\Software\IMVU\dpiScaling`
- Writes the per-user Windows compatibility DPI override for the resolved
  `IMVUClient.exe` path:
  - `HKCU\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers`
  - value: `~ DPIUNAWARE`
- Restores and resizes the IMVU window using the monitor DPI/work-area data.

The important default is:

```python
if args.preset == "lowres":
    args.compat_dpi = "system"
```

That maps to this Windows compatibility flag:

```text
~ DPIUNAWARE
```

In practical terms, Windows DPI-virtualizes IMVU. IMVU behaves as if it is
running on the scaled desktop coordinate space instead of directly targeting a
high-resolution physical panel such as `2880x1800` at `200%`/`250%` scale.
Because Windows then scales the entire IMVU process as one surface, the rendered
UI, mouse hit-testing, room tabs, room overlays, avatar cards, room cards, menus,
and dialog positions are much more likely to stay aligned.

The tradeoff is image quality. Since IMVU is effectively rendered at a lower
logical resolution and then stretched by Windows, the client can look softer or
blurrier than true high-DPI/sharp mode. This is expected. If the in-game
resolution or UI sharpness is not good enough for your setup, use this script as
the stable baseline first, then move on to the deeper patch scripts below.
GPU-level sharpening can also help compensate for the softness without changing
IMVU's internal files.

Why this should be first:

- `fix_imvu_scaling.py` is a Windows-level compatibility fix.
- The other patch scripts are internal IMVU surgery.
- Windows-level scaling keeps IMVU's mixed native/Python/Gecko/scene layers
  together.
- Internal patches can make individual surfaces sharper, but they can also cause
  different layers to scale differently, which is what creates click drift,
  offset overlays, broken avatar cards, room card mismatch, and modal/menu
  alignment problems.

Use the internal patch scripts only when the Windows-level fix works
functionally but the lower-quality scaled output is not acceptable.

---

## 1) Problem Model

When IMVU Classic runs in sharp/high-DPI mode, multiple rendering/input layers can disagree on coordinate systems:

- Native Win32 window layout may be scaled by monitor DPI.
- Embedded Gecko HTML surfaces may be scaled independently.
- Hit-testing can occur in a differently scaled surface than what is rendered.

Observed symptoms include:

- Overlay click targets offset from visual elements.
- In-room overlay hitboxes smaller/larger than drawn content.
- Tab/3D seam artifacts (white line/background bleed).
- Dialog/card content clipping due to double-scaling.

The scripts here treat these as **separate failure classes** and patch each class with isolated changes and explicit backup/restore behavior.

---

## 2) Repository Layout

- `fix_imvu_scaling.py`
  First-try Windows compatibility DPI fix. Does not patch IMVU files; writes
  per-user DPI compatibility registry values and resizes/restores the window.
- `imvu_dpi_runtime_probe.py`  
  Runtime window/DPI probe (JSONL).
- `compare_imvu_probes.py`  
  Focused diff for key room windows (`compatible` vs `sharp`).
- `audit_imvu_dpi_probe.py`  
  Broad audit across visible IMVU child windows; emits Markdown report.
- `patch_imvu_clean_dpi_layout.py`  
  Core layout + Gecko compensation patch for sharp mode.
- `patch_imvu_room_overlay_hitboxes.py`  
  Overlay hitbox tuning (depends on clean-layout Gecko patch).
- `patch_imvu_overlay_click_remap.py`  
  Overlay click remap in packaged UI JS (`imvuContent.jar`).
- `patch_imvu_dialog_scaling.py`  
  HTML dialog/card scaling fix (preserve native sizing, remove harmful CSS transform scale effect).
- `patch_imvu_white_line.py`  
  Tab/3D background seam fix.
- `patch_imvu_emoji.py`  
  Chat emoji rendering, picker, shortcuts, and Twemoji cache — see [Emoji Fix (Start Here)](../README.md#emoji-fix-start-here).
- `emoji_assets/js/*`  
  Emoji JS injected by `patch_imvu_emoji.py`.
- `library_decompiled_structured/im/common.py`  
  Patched `ImMessage` source used when rebuilding `library.zip`.

---

## 3) Environment and Constraints

### Supported runtime assumptions

- OS: Windows 10/11.
- Python: Python 3.x available in PATH.
- Target app: IMVU Classic installed under `%APPDATA%\IMVUClient` (default paths assumed by scripts).
- Permissions: write access to IMVU install/runtime asset directory.

### Files modified by scripts

- `fix_imvu_scaling.py` does not modify IMVU files. It can write per-user
  registry values only:
  - `HKCU\Software\IMVU\dpiScaling`
  - `HKCU\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers`
- `%APPDATA%\IMVUClient\library.zip`
- `%APPDATA%\IMVUClient\ui\chrome\imvuContent.jar`
- Registry keys (optional, for sharp-mode config):
  - `HKCU\Software\IMVU\dpiScaling`
  - `HKCU\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers`

### Safety model

- Every mutating patch script writes a timestamped backup before replacing targets.
- Most scripts block mutation while `IMVUClient.exe` is running (unless `--force` is provided where supported).
- Restore mode is script-specific and restores from latest matching backup suffix.

---

## 4) Instrumentation Pipeline

Use instrumentation before and after patching to detect regressions.

### 4.1 Single/multi-sample runtime capture

```powershell
python .\imvu_dpi_runtime_probe.py --children --out .\compatible_probe.jsonl
python .\imvu_dpi_runtime_probe.py --children --watch --interval 1.0 --out .\sharp_probe.jsonl
```

What is captured per window:

- Process + HWND identity
- Class/title
- Window/client rectangles
- Per-window DPI (`GetDpiForWindow` fallback chain)
- Cursor coordinate conversions (`ScreenToClient`, roundtrip sanity)
- Monitor geometry (`MonitorFromWindow` + `GetMonitorInfoW`)

### 4.2 Focused compare on key room surfaces

```powershell
python .\compare_imvu_probes.py .\compatible_probe.jsonl .\sharp_probe.jsonl
```

Outputs per known key URI:

- Compatible client size
- Sharp client size
- Ratio sharp/compatible for width and height

### 4.3 Broad audit report (Markdown)

```powershell
python .\audit_imvu_dpi_probe.py --baseline .\compatible_probe.jsonl --capture --samples 3 --interval 1.0 --out .\output.md
```

Classification buckets include:

- `ok`
- `under-scaled`
- `over-scaled`
- `small`
- `large`
- `drift`
- `new`
- `missing`

This script groups windows by `(class, normalized-title/URI)` and compares dominant instances by area.

---

## 5) Patch Scripts (Deep Technical)

## 5.1 `patch_imvu_clean_dpi_layout.py` (core patch)

Primary responsibilities:

1. Rebuild `library.zip` from a chosen baseline backup.
2. Patch selected marshalled integer constants in `.pyo` payloads:
   - `toplevelwindow.pyo`: `71 -> 178`
   - `toolstrip.pyo`: `26 -> 65`
   - `HtmlTool.pyo`: `220 -> 550`
3. Replace packaged Gecko context source with a synthesized/patched `imvu/gecko/geckocontext.py`.

Gecko patch behavior:

- Adds DPI scale helper (`dpi / 96.0`).
- Compensates specific overlay URIs by scaling Gecko surface size.
- Includes tab-bar seam overdraw (`+3` height) to hide native/Gecko rounding gap.
- Keeps compensation narrow to selected overlays; avoids global Gecko inflation.

Notable options:

- `--baseline <path>` explicit baseline backup.
- `--restore` restore latest `bak-cleanlayout-*`.
- `--configure-sharp` write registry values for sharp mode.
- `--launch` configure sharp mode and launch IMVU.

Example:

```powershell
python .\patch_imvu_clean_dpi_layout.py --configure-sharp
```

---

## 5.2 `patch_imvu_room_overlay_hitboxes.py`

Purpose:

- Refines `geckocontext.py` compensation for in-room overlays and avatar labels.

Key mechanics:

- Requires clean-layout patch marker to already exist.
- Rewrites `__px13CompensatedRect` block.
- Ensures tab seam patch snippet exists.
- Promotes avatar label compensation to full-size scaling where needed.

Restore source:

- Latest `library.zip.bak-hitbox-*`.

Example:

```powershell
python .\patch_imvu_room_overlay_hitboxes.py
```

---

## 5.3 `patch_imvu_overlay_click_remap.py`

Target: `imvuContent.jar` JavaScript overlays:

- `avatar_menu/AvatarMenu.js`
- `room_widget/RoomWidget.js`

Injected logic:

- Global click listener in capture phase.
- Computes scaled point (`clientX/clientY * 2.5`).
- Uses `document.elementFromPoint` at scaled coords.
- Filters for actionable targets (class/id/cursor heuristics).
- Prevents original event and dispatches synthetic click to remapped target.

Restore source:

- Latest `imvuContent.jar.bak-clickremap-*`.

Example:

```powershell
python .\patch_imvu_overlay_click_remap.py
```

---

## 5.4 `patch_imvu_dialog_scaling.py`

Goal:

- Preserve native dialog sizing while disabling effective Gecko-side over-scaling path for HTML dialogs/cards.

Patch details:

- Rebuilds `imvu/gecko/HTMLDialog/windows.py` from decompiled structured source.
- Fixes known decompiler artifact in `__dialogSpec`.
- Replaces `dpiScaleFactor(...)` usage with `scale = 1.0` in rescale path.
- Drops stale bytecode entry and writes source entry only.

Restore source:

- Latest `library.zip.bak-dialogdpi-*`.

Example:

```powershell
python .\patch_imvu_dialog_scaling.py
```

---

## 5.5 `patch_imvu_white_line.py`

Goal:

- Remove visible seam/background mismatch between tab bar and 3D content areas.

Patch details:

- `tab_bar/TabBar.css`
  - adjusts tab bar height logic (`height: 100%`, `min-height: 68px`)
  - enforces dark background on `html, body`
- `3d/index.html`
  - enforces black background on root/body and scene viewer container

Restore source:

- Latest `imvuContent.jar.bak-whiteline-*`.

Example:

```powershell
python .\patch_imvu_white_line.py
```

---

## 5.6 `patch_imvu_emoji.py`

Chat emoji patch — full documentation, screenshots, and usage are in [Emoji Fix (Start Here)](../README.md#emoji-fix-start-here).

Summary: UTF-8 message decode, Twemoji chat rendering, searchable picker (~1,880 emojis), text shortcuts with replace/append modes, recommendation toggle, and localStorage caching.

```powershell
python .\patch_imvu_emoji.py
```

---

## 6) Recommended End-to-End Runbook

### 6.1 Emoji only (most users)

See [Emoji Fix (Start Here)](../README.md#emoji-fix-start-here). No registry changes, DPI probes, or other patch scripts required.

### 6.2 Safe DPI first runbook

1. Start IMVU normally.
2. Run:
   ```powershell
   python .\fix_imvu_scaling.py
   ```
3. Close and reopen IMVU if the script changed the Windows compatibility DPI
   override.
4. If needed, keep the helper active while testing:
   ```powershell
   python .\fix_imvu_scaling.py --watch
   ```
5. Verify room tabs, overlays, avatar cards, room cards, menus, dialogs, and
   click targets before applying any internal patch script.

If the UI lines up and input works, this is the lowest-risk fix. Expect some
blur/softness because Windows is scaling the final IMVU window output.

If the effective in-game resolution is too low or the softness is unacceptable,
continue with the deep patch runbook below.

### 6.3 Deep patch runbook

1. Close IMVU completely.
2. Capture baseline probe in compatible mode.
3. Apply core patch:
   - `patch_imvu_clean_dpi_layout.py --configure-sharp`
4. Optionally apply targeted patches:
   - `patch_imvu_room_overlay_hitboxes.py`
   - `patch_imvu_overlay_click_remap.py`
   - `patch_imvu_dialog_scaling.py`
   - `patch_imvu_white_line.py`
   - `patch_imvu_emoji.py` (independent of DPI; see [Emoji Fix](../README.md#emoji-fix-start-here).)
5. Relaunch IMVU in sharp mode.
6. Capture sharp probe.
7. Run compare + audit and inspect ratio/classification changes.

If behavior regresses, restore the specific patch family first rather than rolling back everything at once.

---

## 7) Troubleshooting Matrix

- `IMVUClient is running...`  
  Close all IMVU processes; rerun without `--force` when possible.

- `Expected one ... found N` patch errors  
  Your IMVU build likely differs from the expected byte/source signature.  
  Action: collect your current `library.zip`/`imvuContent.jar` signatures and update patch patterns safely.

- `No ... backup found` on restore  
  Script-specific backup suffix not present in target directory.  
  Action: verify path overrides (`--library` / `--jar`) and backup naming family.

- Probe output appears empty  
  IMVU process name/path mismatch.  
  Action: pass explicit `--process` to `imvu_dpi_runtime_probe.py`.

- Chat still shows hex/tofu boxes after emoji patch  
  Patch may not have applied, or IMVU was not restarted.  
  Action: close IMVU, rerun `patch_imvu_emoji.py`, restart client.

- Emoji show as broken images in chat  
  CDN blocked or offline.  
  Action: allow `cdn.jsdelivr.net` and `emojicdn.elk.sh`, or check firewall/VPN.

- `Missing emoji_assets/js/emojiDisplay.js`  
  Clone/download the full repo; the JS asset must be present locally before patching.

- Emoji picker button missing after patch  
  Rerun `patch_imvu_emoji.py` to upgrade an older emoji-only install, then restart IMVU.

- Picker opens but emoji tiles are blank  
  CDN blocked or offline. Allow `cdn.jsdelivr.net` while the picker is open.

- Shortcut suggestions still appear after choosing **Hide**  
  Rerun `patch_imvu_emoji.py` and restart IMVU to pick up the latest JS.

- Append mode still replaces the word  
  Open gear â†’ **Keep word, add emoji after**, then accept with Tab or click the pill.

- `Could not find ImMessage windows-1252 decode line`  
  Your IMVU build differs from expected `library.zip` layout.  
  Action: open an issue with your IMVU version and whether `im/common.pyo` exists.

---

## 8) Development Notes

- Changes are intentionally small, deterministic, and reversible.
- Patch scripts avoid broad binary rewrite logic and instead validate expected signatures before mutation.
- Runtime probes are non-intrusive: no injection, no process memory patching.

---

## 9) Contributing

High-value contributions:

- Additional patch signatures for newer IMVU builds.
- Better URI-key normalization in audit tooling.
- Automated regression harness over saved probe datasets.
- Documentation of behavior across monitor topologies and mixed-DPI setups.

When contributing patches, include:

- IMVU version/build metadata
- Before/after probe JSONL samples
- Expected size-ratio deltas for key windows
- Clear rollback path

---


