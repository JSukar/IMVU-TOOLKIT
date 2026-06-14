import os
import zipfile

from imvu_toolkit import __version__
from imvu_toolkit.patches.emoji import constants as C
from imvu_toolkit.patches.emoji.transforms import (
    build_common_source,
    ensure_emoji_scripts,
    patch_font_css,
    patch_style_css,
    patch_text_file,
)
from imvu_toolkit.paths import asset_path, project_root
from imvu_toolkit.zip_utils import rewrite_zip

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def read_fixture(name):
    with open(os.path.join(FIXTURES, name), "r", encoding="utf-8") as f:
        return f.read()


def test_version():
    assert __version__ == "1.2.3"


def test_project_root_contains_assets():
    root = project_root()
    assert os.path.isdir(os.path.join(root, "emoji_assets", "js"))
    assert os.path.isfile(asset_path("emoji_assets", "js", "emojiDisplay.js"))


def test_build_common_source_patches_decode():
    snippet = read_fixture("common_snippet.py")
    patched = build_common_source(common_text=snippet).decode("utf-8")
    assert C.PATCH_MARKER in patched
    assert "decode('utf-8')" in patched
    assert "windows-1252', 'replace')" in patched


def test_build_common_source_idempotent():
    snippet = read_fixture("common_snippet.py")
    first = build_common_source(common_text=snippet)
    second = build_common_source(common_text=first.decode("utf-8"))
    assert first == second


def test_ensure_emoji_scripts_injects_tags():
    html = read_fixture("chat_index.html")
    patched = ensure_emoji_scripts(html)
    assert "emojiPicker.js" in patched
    assert "emojiCache.js" in patched
    assert "emojiSuggestions.js" in patched


def test_patch_text_file_chat_js():
    js = read_fixture("ChatTool.js")
    patched = patch_text_file(js, "tool/chat/ChatTool.js")
    assert C.LINKIFY_NEW in patched
    assert C.LINKIFY_OLD not in patched


def test_patch_text_file_html_charset():
    html = read_fixture("chat_index.html")
    patched = patch_text_file(html, "tool/chat/index.html")
    assert C.CHARSET_NEW in patched
    assert C.CHARSET_OLD not in patched


def test_patch_style_css_adds_markers():
    css = read_fixture("style.css")
    patched = patch_style_css(css)
    assert C.JS_PATCH_MARKER in patched
    assert C.PICKER_PATCH_MARKER in patched


def test_patch_font_css():
    font = read_fixture("font.css")
    patched = patch_font_css(font)
    assert "Segoe UI Emoji" in patched


def test_emoji_cache_guards_invalid_input():
    source = open(C.EMOJI_CACHE_SOURCE, encoding="utf-8").read()
    assert "normalizeEmojiStr" in source
    assert "if (!emojiStr)" in source
    assert "if (!hex)" in source


def test_rewrite_zip_replaces_entry(tmp_path):
    library = tmp_path / "library.zip"
    with zipfile.ZipFile(library, "w") as zout:
        zout.writestr("im/common.pyo", b"bytecode")
        zout.writestr("im/common.py", b"old")
        zout.writestr("other/file.txt", b"keep")

    backup = rewrite_zip(
        str(library),
        ".bak-test-",
        skip_names={C.ZIP_COMMON_BYTECODE, C.ZIP_COMMON_SOURCE},
        write_entries={C.ZIP_COMMON_SOURCE: b"new-source"},
    )
    assert os.path.isfile(backup)

    with zipfile.ZipFile(library, "r") as zin:
        names = set(zin.namelist())
        assert C.ZIP_COMMON_BYTECODE not in names
        assert zin.read(C.ZIP_COMMON_SOURCE) == b"new-source"
        assert zin.read("other/file.txt") == b"keep"
