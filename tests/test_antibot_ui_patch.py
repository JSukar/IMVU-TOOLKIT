import os

from imvu_toolkit.patches.antibot import constants as C
from imvu_toolkit.patches.antibot.transforms import ensure_antibot_scripts, patch_style_css

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def read_fixture(name):
    with open(os.path.join(FIXTURES, name), "r", encoding="utf-8") as f:
        return f.read()


def test_ensure_antibot_scripts_with_emoji():
    html = read_fixture("tool_chat_index.html")
    patched = ensure_antibot_scripts(html)
    assert "antibotStatus.js" in patched
    assert patched.count("antibotStatus.js") == 1


def test_ensure_antibot_scripts_without_emoji():
    html = read_fixture("chat_index.html")
    patched = ensure_antibot_scripts(html)
    assert "antibotStatus.js" in patched


def test_patch_style_css_adds_marker():
    css = read_fixture("style.css")
    patched = patch_style_css(css)
    assert C.JS_PATCH_MARKER in patched
    assert C.WHITELIST_PATCH_MARKER in patched
    assert ".imvu-antibot-button" in patched
    assert ".imvu-antibot-tab" in patched
    assert ".imvu-antibot-pager" in patched
    assert ".imvu-antibot-whitelist-candidates" in patched


def test_patch_style_css_adds_popup_layout_marker():
    css = read_fixture("style.css")
    patched = patch_style_css(css)
    assert C.POPUP_LAYOUT_MARKER in patched
    assert C.POPUP_LAYOUT_V3_MARKER in patched
    assert C.POPUP_LAYOUT_V4_MARKER in patched
    assert "aria-hidden" in patched


def test_antibot_js_avoids_call_apply():
    with open(C.ANTIBOT_JS_SOURCE, "r", encoding="utf-8") as f:
        js = f.read()
    assert "imvu.call.apply" not in js
