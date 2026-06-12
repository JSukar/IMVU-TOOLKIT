"""Build patched library.zip and imvuContent.jar sources for the room antibot patch."""

from imvu_toolkit.patches.antibot import constants as C


def _read_source(path):
    with open(path, "rb") as f:
        raw = f.read()
    if raw.startswith(b"\xff\xfe"):
        return raw.decode("utf-16-le")
    if raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16-be")
    if len(raw) >= 2 and raw[1:2] == b"\x00" and raw[0:1] != b"\x00":
        try:
            return raw.decode("utf-16-le")
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8")


def _clean_decompiled_source(text):
    """Strip uncompyle6 artifacts that cause SyntaxError at import time."""
    marker = "# okay decompiling"
    if marker in text:
        text = text[: text.index(marker)]
    lines = text.splitlines()
    while lines and not lines[-1].strip():
        lines.pop()
    while lines and lines[-1].strip() == "return":
        lines.pop()
    return "\n".join(lines) + "\n"


def _finalize_source(text, zip_name, validate_compile=False):
    if C.PATCH_MARKER not in text:
        raise RuntimeError("Missing antibot patch marker in %s" % zip_name)
    text = _clean_decompiled_source(text)
    if validate_compile:
        compile(text, zip_name, "exec")
    return text.encode("utf-8")


def build_library_sources():
    entries = {}
    skip_validate = {
        C.ZIP_MEET_SOURCE,
    }
    for zip_name, source_path in C.SOURCE_FILES.items():
        entries[zip_name] = _finalize_source(
            _read_source(source_path),
            zip_name,
            validate_compile=zip_name not in skip_validate,
        )
    return entries


def read_asset(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().encode("utf-8")


def ensure_antibot_scripts(text):
    if "antibotStatus.js" in text:
        return text
    if '<script src="../../js/emojiPicker.js"></script>' in text:
        return text.replace(
            '<script src="../../js/emojiPicker.js"></script>',
            C.ANTIBOT_SCRIPT_AFTER_EMOJI,
            1,
        )
    if C.ANTIBOT_SCRIPT_AFTER_IMVU.split("\n")[0] in text:
        return text.replace(
            '<script src="../../js/imvu.js"></script>',
            C.ANTIBOT_SCRIPT_AFTER_IMVU,
            1,
        )
    raise RuntimeError("Could not inject antibotStatus.js script tag.")


def patch_style_css(text):
    if C.JS_PATCH_MARKER not in text:
        text = text.rstrip() + C.ANTIBOT_CSS + "\n"
    if C.WHITELIST_PATCH_MARKER not in text:
        text = text.rstrip() + C.WHITELIST_CSS + "\n"
    if C.POPUP_LAYOUT_MARKER not in text:
        text = text.rstrip() + C.POPUP_LAYOUT_CSS + "\n"
    if C.POPUP_LAYOUT_V3_MARKER not in text:
        text = text.rstrip() + C.POPUP_LAYOUT_V3_CSS + "\n"
    if C.POPUP_LAYOUT_V4_MARKER not in text:
        text = text.rstrip() + C.POPUP_LAYOUT_V4_CSS + "\n"
    return text


def patch_text_file(text, path):
    if path.endswith(".html"):
        text = ensure_antibot_scripts(text)
    elif path.endswith("style.css"):
        text = patch_style_css(text)
    return text
