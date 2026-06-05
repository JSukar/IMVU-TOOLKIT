import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile


def repo_root():
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def asset_path(*parts):
    return os.path.join(repo_root(), *parts)


DEFAULT_IMVU_DIR = os.path.join(os.environ.get("APPDATA", ""), "IMVUClient")
COMMON_SOURCE = asset_path("library_decompiled_structured", "im", "common.py")
EMOJI_CACHE_SOURCE = asset_path("emoji_assets", "js", "emojiCache.js")
EMOJI_JS_SOURCE = asset_path("emoji_assets", "js", "emojiDisplay.js")
EMOJI_LIST_SOURCE = asset_path("emoji_assets", "js", "emojiList.js")
EMOJI_PICKER_SOURCE = asset_path("emoji_assets", "js", "emojiPicker.js")
EMOJI_SUGGESTIONS_SOURCE = asset_path("emoji_assets", "js", "emojiSuggestions.js")
ZIP_COMMON_SOURCE = "im/common.py"
ZIP_COMMON_BYTECODE = "im/common.pyo"
PATCH_MARKER = "# IMVU emoji/unicode patch"
JS_PATCH_MARKER = "IMVU emoji display patch"
PICKER_PATCH_MARKER = "IMVU emoji picker patch"

FONT_ENTRY = "css/font.css"
FONT_OLD = (
    '    font-family: Arial, "HelveticaNeue", "Helvetica Neue", Helvetica, '
    '"Lucida Grande", sans-serif;'
)
FONT_NEW = (
    '    /* IMVU emoji display patch */\n'
    '    font-family: Arial, "HelveticaNeue", "Helvetica Neue", Helvetica, '
    '"Lucida Grande", "Segoe UI Emoji", "Segoe UI Symbol", sans-serif;'
)

JAR_JS_ENTRIES = {
    "js/emojiCache.js": EMOJI_CACHE_SOURCE,
    "js/emojiDisplay.js": EMOJI_JS_SOURCE,
    "js/emojiList.js": EMOJI_LIST_SOURCE,
    "js/emojiPicker.js": EMOJI_PICKER_SOURCE,
    "js/emojiSuggestions.js": EMOJI_SUGGESTIONS_SOURCE,
}
CHAT_JS_FILES = ("tool/chat/ChatTool.js", "tool/newchat/ChatTool.js")
CHAT_HTML_FILES = ("tool/chat/index.html", "tool/newchat/index.html")
CHAT_STYLE_FILES = ("tool/chat/style.css", "tool/newchat/style.css")

LINKIFY_OLD = "$(messageNode).append(IMVU.Client.util.linkify(msg));"
LINKIFY_NEW = "$(messageNode).append(IMVU.Client.util.linkifyWithEmoji(msg));"

CHARSET_OLD = 'content="text/html; charset=ISO-8859-1"'
CHARSET_NEW = 'content="text/html; charset=UTF-8"'

IMVU_SCRIPT_OLD = '<script src="../../js/imvu.js"></script>'
IMVU_SCRIPT_NEW = (
    '<script src="../../js/imvu.js"></script>\n'
    '        <script src="../../js/emojiCache.js"></script>\n'
    '        <script src="../../js/emojiDisplay.js"></script>\n'
    '        <script src="../../js/emojiList.js"></script>\n'
    '        <script src="../../js/emojiSuggestions.js"></script>\n'
    '        <script src="../../js/emojiPicker.js"></script>'
)
EMOJI_DISPLAY_ONLY = '<script src="../../js/emojiDisplay.js"></script>'
EMOJI_DISPLAY_WITH_PICKER = (
    '<script src="../../js/emojiCache.js"></script>\n'
    '        <script src="../../js/emojiDisplay.js"></script>\n'
    '        <script src="../../js/emojiList.js"></script>\n'
    '        <script src="../../js/emojiSuggestions.js"></script>\n'
    '        <script src="../../js/emojiPicker.js"></script>'
)
EMOJI_SCRIPT_WRONG_ORDER = (
    '<script src="../../js/emojiPicker.js"></script>\n'
    '        <script src="../../js/emojiSuggestions.js"></script>'
)
EMOJI_SCRIPT_RIGHT_ORDER = (
    '<script src="../../js/emojiSuggestions.js"></script>\n'
    '        <script src="../../js/emojiPicker.js"></script>'
)

EMOJI_CSS = """
/* IMVU emoji display patch */
img.emoji-inline {
    height: 1.15em;
    width: 1.15em;
    margin: 0 1px;
    vertical-align: -0.15em;
    border: 0;
}
"""

PICKER_CSS = """
/* IMVU emoji picker patch */
#text-chat.imvu-emoji-picker-root {
    overflow: visible;
}
#input-row-wrapper.imvu-emoji-picker-host {
    overflow: visible;
    z-index: 100;
}
#inputRow .imvu-emoji-button {
    -moz-box-flex: 0;
    display: inline-block;
    width: 34px;
    height: 30px;
    line-height: 28px;
    margin: 3px 0 3px 3px;
    padding: 0;
    border: 1px solid #444;
    background: #222;
    cursor: pointer;
    vertical-align: bottom;
    -moz-user-select: none;
    text-align: center;
}
#inputRow .imvu-emoji-button img {
    width: 22px;
    height: 22px;
    vertical-align: middle;
    border: 0;
}
#inputRow .imvu-emoji-button:hover {
    background: #333;
}
.redesign #inputRow .imvu-emoji-button {
    width: 28px;
    height: 25px;
    line-height: 23px;
    margin: 0 0 0 2px;
    padding: 0;
    border: 0;
    background: #000;
}
.redesign #inputRow .imvu-emoji-button img {
    width: 20px;
    height: 20px;
}
.imvu-emoji-picker {
    position: fixed;
    width: 268px;
    background: #1a1a1a;
    border: 1px solid #555;
    -moz-border-radius: 4px;
    -moz-box-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
    z-index: 999999;
    overflow: visible;
}
.imvu-emoji-picker.hidden {
    display: none;
}
.imvu-emoji-picker-search-wrap {
    position: relative;
    padding: 8px;
    border-bottom: 1px solid #333;
    overflow: visible;
}
.imvu-emoji-picker-search {
    display: block;
    width: auto;
    height: 28px;
    margin-right: 62px;
    -moz-box-sizing: border-box;
    padding: 5px 8px;
    border: 1px solid #444;
    background: #111;
    color: #fff;
    font-size: 12px;
    line-height: 16px;
}
.imvu-emoji-picker-search.hint {
    color: #929292;
}
.imvu-emoji-picker-header-btns {
    position: absolute;
    right: 8px;
    top: 8px;
    width: 58px;
    height: 28px;
    line-height: 28px;
    text-align: right;
    white-space: nowrap;
    z-index: 5;
}
.imvu-emoji-picker-gear,
.imvu-emoji-picker-info {
    display: inline-block;
    width: 26px;
    height: 26px;
    margin: 0 0 0 4px;
    padding: 0;
    border: 1px solid #444;
    background: #222;
    color: #bbb;
    text-align: center;
    cursor: pointer;
    -moz-border-radius: 13px;
    vertical-align: middle;
    overflow: hidden;
    -moz-user-select: none;
}
.imvu-emoji-picker-info {
    font-family: Georgia, "Times New Roman", serif;
    font-style: italic;
    font-weight: bold;
    font-size: 13px;
    line-height: 26px;
}
.imvu-emoji-picker-gear {
    font-family: Arial, sans-serif;
    font-size: 14px;
    line-height: 26px;
    padding-top: 1px;
}
.imvu-emoji-picker-gear:hover,
.imvu-emoji-picker-info:hover {
    background: #333;
    color: #fff;
}
.imvu-emoji-picker-settings {
    position: absolute;
    right: 8px;
    top: 48px;
    min-width: 188px;
    padding: 4px;
    border: 1px solid #555;
    background: #1a1a1a;
    -moz-border-radius: 4px;
    -moz-box-shadow: 0 2px 8px rgba(0, 0, 0, 0.45);
    z-index: 1000000;
}
.imvu-emoji-picker-settings.hidden {
    display: none;
}
.imvu-emoji-picker-about {
    position: absolute;
    right: 8px;
    top: 48px;
    min-width: 180px;
    padding: 8px 10px;
    border: 1px solid #555;
    background: #1a1a1a;
    -moz-border-radius: 4px;
    -moz-box-shadow: 0 2px 8px rgba(0, 0, 0, 0.45);
    z-index: 1000000;
    color: #ccc;
    font-size: 11px;
    line-height: 1.4;
}
.imvu-emoji-picker-about.hidden {
    display: none;
}
.imvu-emoji-picker-about a {
    color: #6eb5ff;
    text-decoration: underline;
}
.imvu-emoji-picker-about a:hover {
    color: #9ecdff;
}
.imvu-emoji-picker-settings-title {
    color: #888;
    font-size: 9px;
    padding: 2px 4px 4px;
    text-transform: uppercase;
}
.imvu-emoji-picker-settings-divider {
    border-top: 1px solid #333;
    margin: 4px 0 2px;
}
.imvu-emoji-picker-settings-mode {
    display: block;
    width: 100%;
    margin: 0 0 2px 0;
    padding: 4px 6px;
    border: 0;
    background: transparent;
    color: #ccc;
    font-size: 10px;
    text-align: left;
    cursor: pointer;
    -moz-border-radius: 3px;
}
.imvu-emoji-picker-settings-mode:hover {
    background: #333;
}
.imvu-emoji-picker-settings-mode.active {
    background: #444;
    color: #fff;
}
.imvu-emoji-picker-tabs {
    padding: 4px 6px 3px;
    border-bottom: 1px solid #333;
    white-space: nowrap;
    overflow-x: auto;
    overflow-y: hidden;
    height: 28px;
    line-height: 20px;
    background: #1a1a1a;
}
.imvu-emoji-picker-tab {
    display: inline-block;
    margin: 0 2px 0 0;
    padding: 2px 6px;
    border: 0;
    background: transparent;
    color: #aaa;
    font-size: 11px;
    cursor: pointer;
    -moz-border-radius: 2px;
    line-height: 18px;
}
.imvu-emoji-picker-tab.active {
    background: #333;
    color: #fff;
}
.imvu-emoji-picker-grid-wrap {
    height: 240px;
    min-height: 80px;
    overflow-y: auto;
    overflow-x: hidden;
    background: #1a1a1a;
    -moz-border-radius: 0 0 4px 4px;
}
.imvu-emoji-picker-grid {
    padding: 4px;
    line-height: 0;
}
.imvu-emoji-picker-item {
    width: 32px;
    height: 32px;
    margin: 0;
    padding: 2px;
    border: 0;
    background: transparent;
    cursor: pointer;
    -moz-border-radius: 2px;
    display: inline-block;
    vertical-align: top;
    line-height: 0;
    text-align: center;
}
.imvu-emoji-picker-item:hover {
    background: #333;
}
.imvu-emoji-picker-item img {
    width: 28px;
    height: 28px;
    border: 0;
    vertical-align: middle;
}
.imvu-emoji-picker-item-fallback {
    display: inline-block;
    width: 28px;
    height: 28px;
    line-height: 28px;
    font-size: 16px;
    text-align: center;
    vertical-align: middle;
}
.imvu-emoji-picker-empty {
    color: #888;
    font-size: 11px;
    padding: 10px;
    text-align: center;
}
.imvu-emoji-suggest-host {
    position: absolute;
    left: 4px;
    bottom: 100%;
    margin-bottom: 2px;
    z-index: 9998;
    white-space: nowrap;
}
.imvu-emoji-suggest {
    display: inline-block;
    vertical-align: middle;
}
.imvu-emoji-suggest.hidden {
    display: none;
}
.imvu-emoji-suggest-btn {
    display: inline-block;
    margin: 0;
    padding: 3px 8px;
    border: 1px solid #555;
    background: #222;
    color: #ddd;
    font-size: 11px;
    cursor: pointer;
    -moz-border-radius: 12px;
    -moz-box-shadow: 0 1px 6px rgba(0, 0, 0, 0.45);
    line-height: 20px;
    vertical-align: middle;
}
.imvu-emoji-suggest-btn:hover {
    background: #333;
    border-color: #777;
}
.imvu-emoji-suggest-word {
    font-weight: bold;
    color: #fff;
    margin-right: 4px;
}
.imvu-emoji-suggest-arrow {
    color: #888;
    margin-right: 4px;
}
.imvu-emoji-suggest-img {
    width: 18px;
    height: 18px;
    vertical-align: middle;
    border: 0;
}
"""


def parse_args():
    parser = argparse.ArgumentParser(description="Patch IMVU chat emoji rendering.")
    parser.add_argument("--imvu-dir", default=DEFAULT_IMVU_DIR)
    parser.add_argument("--library", help="Path to library.zip (overrides --imvu-dir).")
    parser.add_argument("--content-jar", help="Path to imvuContent.jar (overrides --imvu-dir).")
    parser.add_argument("--restore", action="store_true")
    parser.add_argument("--force", action="store_true", help="Patch even if IMVU appears to be running.")
    parser.add_argument(
        "--no-close-imvu",
        action="store_true",
        help="Do not automatically close IMVU before patching.",
    )
    return parser.parse_args()


def library_path(args):
    if args.library:
        return os.path.abspath(args.library)
    return os.path.join(args.imvu_dir, "library.zip")


def content_jar_path(args):
    if args.content_jar:
        return os.path.abspath(args.content_jar)
    return os.path.join(args.imvu_dir, "ui", "chrome", "imvuContent.jar")


def imvu_client_processes(imvu_dir):
    imvu_dir = os.path.abspath(imvu_dir).lower()
    processes = []
    try:
        output = subprocess.check_output(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-Process IMVUClient -ErrorAction SilentlyContinue | "
                "ForEach-Object { $_.Id.ToString() + '|' + $_.Path }",
            ],
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except Exception:
        return processes
    for line in output.splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        pid_text, path = line.split("|", 1)
        path = path.strip()
        if path and os.path.dirname(path).lower() == imvu_dir:
            try:
                processes.append((int(pid_text), path))
            except ValueError:
                continue
    return processes


def imvu_is_running(imvu_dir):
    return bool(imvu_client_processes(imvu_dir))


def close_imvu(imvu_dir, timeout=20):
    processes = imvu_client_processes(imvu_dir)
    if not processes:
        return True, None

    for pid, path in processes:
        print("Closing IMVUClient (PID %d)..." % pid)
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    deadline = time.time() + timeout
    while time.time() < deadline:
        if not imvu_is_running(imvu_dir):
            return True, None
        time.sleep(0.5)

    return False, "IMVUClient is still running. Close it manually and try again."


def ensure_imvu_closed(imvu_dir, force, no_close_imvu):
    if not imvu_is_running(imvu_dir):
        return True, None

    if force:
        return True, None

    if no_close_imvu:
        return False, "IMVUClient is running. Close IMVU or rerun without --no-close-imvu."

    print("IMVU is running. Closing it automatically...")
    ok, err = close_imvu(imvu_dir)
    if ok:
        print("IMVU closed.")
        return True, None
    return False, err


def newest_backup(target, prefix):
    matches = sorted(glob.glob(target + prefix + "*"))
    return matches[-1] if matches else None


def build_common_source():
    with open(COMMON_SOURCE, "r", encoding="utf-8") as f:
        text = f.read()

    if PATCH_MARKER not in text:
        old = "            self.__message = message.decode('windows-1252')"
        new = """            # IMVU emoji/unicode patch: prefer UTF-8, fall back to legacy chat encoding.
            try:
                self.__message = message.decode('utf-8')
            except UnicodeDecodeError:
                self.__message = message.decode('windows-1252', 'replace')"""
        if text.count(old) != 1:
            raise RuntimeError("Could not find ImMessage windows-1252 decode line.")
        text = text.replace(old, new, 1)

    stripped = text.rstrip()
    if stripped.endswith("\nreturn"):
        text = stripped[:-len("\nreturn")] + "\n"

    compile(text, ZIP_COMMON_SOURCE, "exec")
    return text.encode("utf-8")


def read_asset(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().encode("utf-8")


def ensure_emoji_scripts(text):
    if "emojiCache.js" not in text and "emojiDisplay.js" in text:
        text = text.replace(
            '<script src="../../js/emojiDisplay.js"></script>',
            '<script src="../../js/emojiCache.js"></script>\n'
            '        <script src="../../js/emojiDisplay.js"></script>',
            1,
        )
    if EMOJI_SCRIPT_WRONG_ORDER in text:
        text = text.replace(EMOJI_SCRIPT_WRONG_ORDER, EMOJI_SCRIPT_RIGHT_ORDER, 1)
    if "emojiSuggestions.js" not in text and "emojiPicker.js" in text:
        text = text.replace(
            '<script src="../../js/emojiPicker.js"></script>',
            '<script src="../../js/emojiSuggestions.js"></script>\n'
            '        <script src="../../js/emojiPicker.js"></script>',
            1,
        )
    if "emojiPicker.js" in text:
        return text
    if EMOJI_DISPLAY_ONLY in text:
        return text.replace(EMOJI_DISPLAY_ONLY, EMOJI_DISPLAY_WITH_PICKER, 1)
    if IMVU_SCRIPT_OLD in text and "emojiDisplay.js" not in text:
        return text.replace(IMVU_SCRIPT_OLD, IMVU_SCRIPT_NEW, 1)
    if "emojiDisplay.js" not in text:
        raise RuntimeError("Could not inject emoji script tags.")
    return text


def patch_style_css(text):
    if JS_PATCH_MARKER not in text:
        text = text.rstrip() + EMOJI_CSS + "\n"

    marker = "/* IMVU emoji picker patch */"
    if marker in text:
        idx = text.index(marker)
        text = text[:idx].rstrip() + "\n" + PICKER_CSS + "\n"
    elif PICKER_PATCH_MARKER not in text:
        text = text.rstrip() + PICKER_CSS + "\n"
    return text


def patch_text_file(text, path):
    if path.endswith(".js"):
        if LINKIFY_OLD not in text:
            if LINKIFY_NEW in text:
                return text
            raise RuntimeError("%s: missing linkify append line" % path)
        if text.count(LINKIFY_OLD) != 1:
            raise RuntimeError("%s: expected one linkify append, found %s" % (path, text.count(LINKIFY_OLD)))
        text = text.replace(LINKIFY_OLD, LINKIFY_NEW, 1)

    elif path.endswith(".html"):
        if CHARSET_OLD in text:
            text = text.replace(CHARSET_OLD, CHARSET_NEW, 1)
        text = ensure_emoji_scripts(text)

    elif path.endswith("style.css"):
        text = patch_style_css(text)

    return text


def patch_font_css(font_text):
    if "Segoe UI Emoji" in font_text:
        return font_text
    if font_text.count(FONT_OLD) != 1:
        raise RuntimeError("Could not find expected font-family line in %s" % FONT_ENTRY)
    return font_text.replace(FONT_OLD, FONT_NEW, 1)


def patch_content_jar(jar_path):
    backup = "%s.bak-emoji-%s" % (jar_path, time.strftime("%Y%m%d-%H%M%S"))
    shutil.copy2(jar_path, backup)

    fd, temp_path = tempfile.mkstemp(
        prefix="imvuContent.emoji.",
        suffix=".jar",
        dir=os.path.dirname(os.path.abspath(jar_path)),
    )
    os.close(fd)

    overrides = {}
    for jar_entry, source_path in JAR_JS_ENTRIES.items():
        overrides[jar_entry] = read_asset(source_path)

    try:
        with zipfile.ZipFile(jar_path, "r") as zin:
            for info in zin.infolist():
                name = info.filename
                if name in overrides:
                    continue
                if name == FONT_ENTRY:
                    overrides[name] = patch_font_css(zin.read(name).decode("utf-8")).encode("utf-8")
                    continue
                if name in CHAT_JS_FILES + CHAT_HTML_FILES + CHAT_STYLE_FILES:
                    overrides[name] = patch_text_file(zin.read(name).decode("utf-8"), name).encode("utf-8")
                    continue

            payloads = []
            for info in zin.infolist():
                if info.filename in overrides:
                    continue
                payloads.append((info, zin.read(info.filename)))

        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for info, data in payloads:
                zout.writestr(info, data)
            for name, data in overrides.items():
                info = zipfile.ZipInfo(name, time.localtime(time.time())[:6])
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                zout.writestr(info, data)

        os.chmod(jar_path, 0o666)
        os.replace(temp_path, jar_path)
        return backup
    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise


def patch_library(library, patched_source):
    backup = "%s.bak-emoji-%s" % (library, time.strftime("%Y%m%d-%H%M%S"))
    shutil.copy2(library, backup)

    fd, temp_path = tempfile.mkstemp(
        prefix="library.emoji.",
        suffix=".zip",
        dir=os.path.dirname(os.path.abspath(library)),
    )
    os.close(fd)

    try:
        with zipfile.ZipFile(library, "r") as zin:
            payloads = []
            for info in zin.infolist():
                if info.filename in (ZIP_COMMON_BYTECODE, ZIP_COMMON_SOURCE):
                    continue
                payloads.append((info, zin.read(info.filename)))

        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for info, data in payloads:
                zout.writestr(info, data)
            info = zipfile.ZipInfo(ZIP_COMMON_SOURCE, time.localtime(time.time())[:6])
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zout.writestr(info, patched_source)

        os.chmod(library, 0o666)
        os.replace(temp_path, library)
        return backup
    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise


def restore_library(library):
    backup = newest_backup(library, ".bak-emoji-")
    if not backup:
        raise RuntimeError("No emoji backup found for %s" % library)
    shutil.copy2(backup, library)
    return backup


def restore_jar(jar_path):
    backup = newest_backup(jar_path, ".bak-emoji-")
    if not backup:
        raise RuntimeError("No emoji backup found for %s" % jar_path)
    shutil.copy2(backup, jar_path)
    return backup


def main():
    args = parse_args()
    library = library_path(args)
    jar_path = content_jar_path(args)
    imvu_dir = os.path.dirname(library)

    for path in JAR_JS_ENTRIES.values():
        if path == COMMON_SOURCE:
            continue
        if not os.path.exists(path):
            print("Missing %s" % path, file=sys.stderr)
            return 1
    if not os.path.exists(COMMON_SOURCE):
        print("Missing %s" % COMMON_SOURCE, file=sys.stderr)
        return 1

    if not os.path.exists(library):
        print("Missing library.zip: %s" % library, file=sys.stderr)
        return 1
    if not os.path.exists(jar_path):
        print("Missing imvuContent.jar: %s" % jar_path, file=sys.stderr)
        return 1

    ok, err = ensure_imvu_closed(imvu_dir, args.force, args.no_close_imvu)
    if not ok:
        print(err, file=sys.stderr)
        return 2

    if args.restore:
        lib_backup = restore_library(library)
        jar_backup = restore_jar(jar_path)
        print("Restored %s from %s" % (library, lib_backup))
        print("Restored %s from %s" % (jar_path, jar_backup))
        return 0

    common_source = build_common_source()
    lib_backup = patch_library(library, common_source)
    jar_backup = patch_content_jar(jar_path)
    print("Patched chat message UTF-8 decoding in %s" % library)
    print("Library backup: %s" % lib_backup)
    print("Patched Twemoji chat rendering + emoji picker in %s" % jar_path)
    print("Content backup: %s" % jar_backup)
    print("Restart IMVU to load the changes.")
    print("Note: emoji images load from jsDelivr (internet required in chat).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
