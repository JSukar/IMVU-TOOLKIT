"""Text and asset transforms for the IMVU emoji patch."""

from imvu_toolkit.patches.emoji import constants as C

ANTIBOT_SCRIPT = '<script src="../../js/antibotStatus.js"></script>'


def _restore_antibot_script(text, had_antibot):
    """Re-attach antibotStatus.js after emojiPicker when emoji injects broke it."""
    if not had_antibot or ANTIBOT_SCRIPT in text:
        return text
    picker = '<script src="../../js/emojiPicker.js"></script>'
    if picker not in text:
        return text
    return text.replace(picker, picker + "\n        " + ANTIBOT_SCRIPT, 1)


def build_common_source(common_source_path=None, common_text=None):
    if common_text is None:
        with open(common_source_path or C.COMMON_SOURCE, "r", encoding="utf-8") as f:
            common_text = f.read()

    if C.PATCH_MARKER not in common_text:
        old = "            self.__message = message.decode('windows-1252')"
        new = (
            "            # IMVU emoji/unicode patch: prefer UTF-8, fall back to legacy chat encoding.\n"  # noqa: E501
            "            try:\n"
            "                self.__message = message.decode('utf-8')\n"
            "            except UnicodeDecodeError:\n"
            "                self.__message = message.decode('windows-1252', 'replace')"
        )
        if common_text.count(old) != 1:
            raise RuntimeError("Could not find ImMessage windows-1252 decode line.")
        common_text = common_text.replace(old, new, 1)

    stripped = common_text.rstrip()
    if stripped.endswith("\nreturn"):
        common_text = stripped[: -len("\nreturn")] + "\n"

    compile(common_text, C.ZIP_COMMON_SOURCE, "exec")
    return common_text.encode("utf-8")


def read_asset(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().encode("utf-8")


def ensure_emoji_scripts(text):
    had_antibot = "antibotStatus.js" in text

    if "emojiCache.js" not in text and "emojiDisplay.js" in text:
        text = text.replace(
            '<script src="../../js/emojiDisplay.js"></script>',
            '<script src="../../js/emojiCache.js"></script>\n'
            '        <script src="../../js/emojiDisplay.js"></script>',
            1,
        )
    if C.EMOJI_SCRIPT_WRONG_ORDER in text:
        text = text.replace(C.EMOJI_SCRIPT_WRONG_ORDER, C.EMOJI_SCRIPT_RIGHT_ORDER, 1)
    if "emojiSuggestions.js" not in text and "emojiPicker.js" in text:
        text = text.replace(
            '<script src="../../js/emojiPicker.js"></script>',
            '<script src="../../js/emojiSuggestions.js"></script>\n'
            '        <script src="../../js/emojiPicker.js"></script>',
            1,
        )
    if "emojiPicker.js" in text:
        return _restore_antibot_script(text, had_antibot)
    if C.EMOJI_DISPLAY_ONLY in text:
        text = text.replace(C.EMOJI_DISPLAY_ONLY, C.EMOJI_DISPLAY_WITH_PICKER, 1)
        return _restore_antibot_script(text, had_antibot)
    if C.IMVU_SCRIPT_OLD in text and "emojiDisplay.js" not in text:
        text = text.replace(C.IMVU_SCRIPT_OLD, C.IMVU_SCRIPT_NEW, 1)
        return _restore_antibot_script(text, had_antibot)
    if "emojiDisplay.js" not in text:
        raise RuntimeError("Could not inject emoji script tags.")
    return _restore_antibot_script(text, had_antibot)


def patch_style_css(text):
    if C.JS_PATCH_MARKER not in text:
        text = text.rstrip() + C.EMOJI_CSS + "\n"

    marker = "/* IMVU emoji picker patch */"
    if marker in text:
        idx = text.index(marker)
        text = text[:idx].rstrip() + "\n" + C.PICKER_CSS + "\n"
    elif C.PICKER_PATCH_MARKER not in text:
        text = text.rstrip() + C.PICKER_CSS + "\n"
    return text


def patch_text_file(text, path):
    if path.endswith(".js"):
        if C.LINKIFY_OLD not in text:
            if C.LINKIFY_NEW in text:
                return text
            raise RuntimeError("%s: missing linkify append line" % path)
        if text.count(C.LINKIFY_OLD) != 1:
            raise RuntimeError(
                "%s: expected one linkify append, found %s" % (path, text.count(C.LINKIFY_OLD))
            )
        text = text.replace(C.LINKIFY_OLD, C.LINKIFY_NEW, 1)

    elif path.endswith(".html"):
        if C.CHARSET_OLD in text:
            text = text.replace(C.CHARSET_OLD, C.CHARSET_NEW, 1)
        text = ensure_emoji_scripts(text)

    elif path.endswith("style.css"):
        text = patch_style_css(text)

    return text


def patch_font_css(font_text):
    if "Segoe UI Emoji" in font_text:
        return font_text
    if font_text.count(C.FONT_OLD) != 1:
        raise RuntimeError("Could not find expected font-family line in %s" % C.FONT_ENTRY)
    return font_text.replace(C.FONT_OLD, C.FONT_NEW, 1)
