from imvu_toolkit.paths import asset_path

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
BACKUP_PREFIX = ".bak-emoji-"

FONT_ENTRY = "css/font.css"
FONT_OLD = (
    '    font-family: Arial, "HelveticaNeue", "Helvetica Neue", Helvetica, '
    '"Lucida Grande", sans-serif;'
)
FONT_NEW = (
    "    /* IMVU emoji display patch */\n"
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
    margin-right: 92px;
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
    width: 88px;
    height: 28px;
    line-height: 28px;
    text-align: right;
    white-space: nowrap;
    z-index: 5;
}
.imvu-emoji-picker-gear,
.imvu-emoji-picker-info,
.imvu-emoji-picker-fav-header {
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
.imvu-emoji-picker-fav-header {
    font-family: Arial, sans-serif;
    font-size: 14px;
    line-height: 26px;
    padding-top: 1px;
    color: #bbb;
}
.imvu-emoji-picker-fav-header.active,
.imvu-emoji-picker-fav-header:hover {
    color: #f5c542;
    background: #333;
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
.imvu-emoji-picker-cell {
    position: relative;
    display: inline-block;
    width: 32px;
    height: 32px;
    vertical-align: top;
}
.imvu-emoji-picker-item {
    width: 28px;
    height: 28px;
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
.imvu-emoji-picker-fav-toggle {
    position: absolute;
    right: 0;
    top: 0;
    width: 14px;
    height: 14px;
    margin: 0;
    padding: 0;
    border: 0;
    line-height: 14px;
    font-size: 11px;
    color: #777;
    background: #1a1a1a;
    cursor: pointer;
    text-align: center;
    z-index: 2;
}
.imvu-emoji-picker-fav-toggle.active,
.imvu-emoji-picker-fav-toggle:hover {
    color: #f5c542;
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
