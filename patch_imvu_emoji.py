#!/usr/bin/env python3
"""Patch IMVU Classic so chat emoji render instead of tofu/hex boxes.

IMVU uses Gecko 1.9 (Firefox 3 era), which cannot paint modern color emoji fonts.
This patch:
  1. library.zip — decode chat bytes as UTF-8 first.
  2. imvuContent.jar — Twemoji <img> replacement in chat + UTF-8 page charset.
"""

import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile


DEFAULT_IMVU_DIR = r"C:\Users\Null\AppData\Roaming\IMVUClient"
COMMON_SOURCE = os.path.join("library_decompiled_structured", "im", "common.py")
EMOJI_JS_SOURCE = os.path.join("emoji_assets", "js", "emojiDisplay.js")
ZIP_COMMON_SOURCE = "im/common.py"
ZIP_COMMON_BYTECODE = "im/common.pyo"
PATCH_MARKER = "# IMVU emoji/unicode patch"
JS_PATCH_MARKER = "IMVU emoji display patch"

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

JAR_JS_ENTRY = "js/emojiDisplay.js"
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
    '        <script src="../../js/emojiDisplay.js"></script>'
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


def parse_args():
    parser = argparse.ArgumentParser(description="Patch IMVU chat emoji rendering.")
    parser.add_argument("--imvu-dir", default=DEFAULT_IMVU_DIR)
    parser.add_argument("--library", help="Path to library.zip (overrides --imvu-dir).")
    parser.add_argument("--content-jar", help="Path to imvuContent.jar (overrides --imvu-dir).")
    parser.add_argument("--restore", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def library_path(args):
    if args.library:
        return os.path.abspath(args.library)
    return os.path.join(args.imvu_dir, "library.zip")


def content_jar_path(args):
    if args.content_jar:
        return os.path.abspath(args.content_jar)
    return os.path.join(args.imvu_dir, "ui", "chrome", "imvuContent.jar")


def imvu_is_running(imvu_dir):
    imvu_dir = os.path.abspath(imvu_dir).lower()
    try:
        output = subprocess.check_output(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-Process IMVUClient -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Path",
            ],
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except Exception:
        return False
    for line in output.splitlines():
        path = line.strip()
        if path and os.path.dirname(path).lower() == imvu_dir:
            return True
    return False


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


def read_emoji_js():
    with open(EMOJI_JS_SOURCE, "r", encoding="utf-8") as f:
        return f.read().encode("utf-8")


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
        if IMVU_SCRIPT_OLD in text and "emojiDisplay.js" not in text:
            text = text.replace(IMVU_SCRIPT_OLD, IMVU_SCRIPT_NEW, 1)
        elif "emojiDisplay.js" not in text:
            raise RuntimeError("%s: could not inject emojiDisplay.js script tag" % path)

    elif path.endswith("style.css"):
        if JS_PATCH_MARKER not in text:
            text = text.rstrip() + EMOJI_CSS + "\n"

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

    emoji_js = read_emoji_js()
    overrides = {JAR_JS_ENTRY: emoji_js}

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

    if not os.path.exists(library):
        print("Missing library.zip: %s" % library, file=sys.stderr)
        return 1
    if not os.path.exists(jar_path):
        print("Missing imvuContent.jar: %s" % jar_path, file=sys.stderr)
        return 1
    if not os.path.exists(EMOJI_JS_SOURCE):
        print("Missing %s" % EMOJI_JS_SOURCE, file=sys.stderr)
        return 1

    if imvu_is_running(imvu_dir) and not args.force:
        print("IMVUClient is running. Close IMVU completely, then rerun this script.", file=sys.stderr)
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
    print("Patched Twemoji chat rendering in %s" % jar_path)
    print("Content backup: %s" % jar_backup)
    print("Restart IMVU to load the changes.")
    print("Note: emoji images load from jsDelivr (internet required in chat).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
