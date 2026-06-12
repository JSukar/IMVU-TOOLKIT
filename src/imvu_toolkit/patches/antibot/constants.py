from imvu_toolkit.paths import asset_path

PATCH_MARKER = "# IMVU room antibot patch"
JS_PATCH_MARKER = "IMVU room antibot patch"
WHITELIST_PATCH_MARKER = "IMVU antibot whitelist UI"
POPUP_LAYOUT_MARKER = "IMVU antibot popup layout v2"
POPUP_LAYOUT_V3_MARKER = "IMVU antibot popup layout v3"
POPUP_LAYOUT_V4_MARKER = "IMVU antibot popup layout v4"
BACKUP_PREFIX = ".bak-antibot-"

ZIP_ANTIBOT_SOURCE = "im/antibot.py"
ZIP_MEET_SOURCE = "im/meet.py"
ZIP_MEET_BYTECODE = "im/meet.pyo"
ZIP_SESSION_DISPATCHER_SOURCE = "imvu/session/SessionDispatcher.py"
ZIP_SESSION_DISPATCHER_BYTECODE = "imvu/session/SessionDispatcher.pyo"
ZIP_SESSIONWINDOW_SOURCE = "imvu/client/sessionwindow.py"
ZIP_SESSIONWINDOW_BYTECODE = "imvu/client/sessionwindow.pyo"
ZIP_CHAT_TOOL_SOURCE = "imvu/tool/ChatTool.py"
SESSIONWINDOW_ZIP_ENTRIES = (
    ZIP_SESSIONWINDOW_SOURCE,
    ZIP_SESSIONWINDOW_BYTECODE,
)
ZIP_CHAT_TOOL_BYTECODE = "imvu/tool/ChatTool.pyo"

ANTIBOT_SOURCE = asset_path("library_decompiled_structured", "im", "antibot.py")
MEET_SOURCE = asset_path("library_decompiled_structured", "im", "meet.py")
SESSION_DISPATCHER_SOURCE = asset_path(
    "library_decompiled_structured", "imvu", "session", "SessionDispatcher.py"
)
CHAT_TOOL_SOURCE = asset_path(
    "library_decompiled_structured", "imvu", "tool", "ChatTool.py"
)
ANTIBOT_JS_SOURCE = asset_path("antibot_assets", "js", "antibotStatus.js")

SOURCE_FILES = {
    ZIP_ANTIBOT_SOURCE: ANTIBOT_SOURCE,
    ZIP_MEET_SOURCE: MEET_SOURCE,
    ZIP_SESSION_DISPATCHER_SOURCE: SESSION_DISPATCHER_SOURCE,
    ZIP_CHAT_TOOL_SOURCE: CHAT_TOOL_SOURCE,
}

SKIP_BYTECODE = (
    ZIP_MEET_BYTECODE,
    ZIP_MEET_SOURCE,
    ZIP_SESSION_DISPATCHER_BYTECODE,
    ZIP_SESSION_DISPATCHER_SOURCE,
    ZIP_CHAT_TOOL_BYTECODE,
    ZIP_CHAT_TOOL_SOURCE,
    ZIP_ANTIBOT_SOURCE,
)

JAR_JS_ENTRIES = {
    "js/antibotStatus.js": ANTIBOT_JS_SOURCE,
}
CHAT_HTML_FILES = ("tool/chat/index.html", "tool/newchat/index.html")
CHAT_STYLE_FILES = ("tool/chat/style.css", "tool/newchat/style.css")

ANTIBOT_SCRIPT_TAG = '<script src="../../js/antibotStatus.js"></script>'
ANTIBOT_SCRIPT_AFTER_EMOJI = (
    '<script src="../../js/emojiPicker.js"></script>\n'
    '        <script src="../../js/antibotStatus.js"></script>'
)
ANTIBOT_SCRIPT_AFTER_IMVU = (
    '<script src="../../js/imvu.js"></script>\n'
    '        <script src="../../js/antibotStatus.js"></script>'
)

ANTIBOT_CSS = """
/* IMVU room antibot patch */
#inputRow .imvu-antibot-button {
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
#inputRow .imvu-antibot-button .imvu-antibot-icon {
    font-size: 16px;
    line-height: 28px;
}
#inputRow .imvu-antibot-button.active {
    border-color: #39d353;
    background: #14381a;
    box-shadow: 0 0 8px rgba(57, 211, 83, 0.45);
    opacity: 1;
}
#inputRow .imvu-antibot-button.active .imvu-antibot-icon {
    filter: none;
    opacity: 1;
}
#inputRow .imvu-antibot-button.active .imvu-antibot-on {
    display: inline-block;
    color: #39d353;
    font-size: 9px;
    font-weight: bold;
    margin-left: 1px;
    vertical-align: top;
    line-height: 28px;
}
#inputRow .imvu-antibot-button.inactive {
    opacity: 0.55;
}
#inputRow .imvu-antibot-button.inactive .imvu-antibot-icon {
    filter: grayscale(1);
}
#inputRow .imvu-antibot-button:hover {
    background: #333;
}
.redesign #inputRow .imvu-antibot-button {
    width: 28px;
    height: 25px;
    line-height: 23px;
    margin: 0 0 0 2px;
    border: 0;
    background: #000;
}
.redesign #inputRow .imvu-antibot-button .imvu-antibot-icon {
    font-size: 14px;
    line-height: 23px;
}
.imvu-antibot-popup {
    position: fixed;
    width: 280px;
    max-height: 320px;
    background: #1a1a1a;
    border: 1px solid #555;
    -moz-border-radius: 4px;
    -moz-box-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
    z-index: 999999;
    overflow: hidden;
}
.imvu-antibot-popup.hidden {
    display: none;
}
.imvu-antibot-popup-title {
    padding: 8px 10px;
    border-bottom: 1px solid #333;
    color: #ddd;
    font-size: 12px;
    font-weight: bold;
}
.imvu-antibot-popup-body {
    max-height: 250px;
    overflow-y: auto;
    padding: 6px 0;
}
.imvu-antibot-list {
    list-style: none;
    margin: 0;
    padding: 0;
}
.imvu-antibot-list li {
    position: relative;
    padding: 6px 10px;
    padding-right: 56px;
    border-bottom: 1px solid #2a2a2a;
}
.imvu-antibot-name {
    display: block;
    color: #fff;
    font-size: 12px;
}
.imvu-antibot-reason {
    display: block;
    color: #888;
    font-size: 10px;
    margin-top: 2px;
}
.imvu-antibot-empty {
    color: #888;
    font-size: 11px;
    line-height: 1.45;
    padding: 10px;
    text-align: center;
}
"""

WHITELIST_CSS = """
/* IMVU antibot whitelist UI */
.imvu-antibot-tabs {
    padding: 6px 8px 0;
    border-bottom: 1px solid #333;
    white-space: nowrap;
}
.imvu-antibot-tab {
    display: inline-block;
    margin: 0 4px 0 0;
    padding: 4px 8px;
    border: 0;
    background: transparent;
    color: #aaa;
    font-size: 11px;
    cursor: pointer;
    -moz-border-radius: 3px 3px 0 0;
}
.imvu-antibot-tab.active {
    background: #333;
    color: #fff;
}
.imvu-antibot-panel.hidden {
    display: none;
}
.imvu-antibot-whitelist-add {
    padding: 8px;
    border-bottom: 1px solid #333;
}
.imvu-antibot-whitelist-add label {
    display: block;
    color: #888;
    font-size: 10px;
    margin-bottom: 4px;
}
.imvu-antibot-whitelist-candidates {
    max-height: 110px;
    overflow-y: auto;
}
.imvu-antibot-whitelist-candidates .imvu-antibot-empty-row {
    color: #888;
    font-size: 11px;
    padding-right: 10px;
}
.imvu-antibot-pager {
    padding: 6px 10px 4px;
    color: #888;
    font-size: 10px;
    border-bottom: 1px solid #2a2a2a;
}
.imvu-antibot-page-btn {
    display: inline-block;
    margin: 0 0 0 6px;
    padding: 2px 6px;
    border: 1px solid #555;
    background: #222;
    color: #ddd;
    font-size: 10px;
    cursor: pointer;
    -moz-border-radius: 3px;
}
.imvu-antibot-page-btn:hover {
    background: #333;
}
.imvu-antibot-trusted-label {
    color: #6a6;
    font-size: 10px;
}
.imvu-antibot-whitelist-add-row {
    display: block;
    white-space: nowrap;
}
.imvu-antibot-whitelist-select {
    width: 170px;
    height: 24px;
    margin: 0 4px 0 0;
    border: 1px solid #444;
    background: #111;
    color: #fff;
    font-size: 11px;
}
.imvu-antibot-whitelist-add-btn,
.imvu-antibot-trust-btn,
.imvu-antibot-remove-btn {
    display: inline-block;
    margin: 0;
    padding: 3px 8px;
    border: 1px solid #555;
    background: #222;
    color: #ddd;
    font-size: 10px;
    cursor: pointer;
    -moz-border-radius: 3px;
    vertical-align: middle;
}
.imvu-antibot-whitelist-add-btn:hover,
.imvu-antibot-trust-btn:hover,
.imvu-antibot-remove-btn:hover {
    background: #333;
}
.imvu-antibot-list-actions {
    position: absolute;
    right: 8px;
    top: 50%;
    margin-top: -11px;
}
.imvu-antibot-badge {
    display: inline-block;
    margin-left: 6px;
    padding: 1px 5px;
    border-radius: 8px;
    background: #333;
    color: #aaa;
    font-size: 9px;
    vertical-align: middle;
}
"""

POPUP_LAYOUT_CSS = """
/* IMVU antibot popup layout v2 */
#text-chat.imvu-antibot-root,
.imvu-antibot-anchor {
    position: relative;
}
.imvu-antibot-popup {
    position: absolute;
    right: 0;
    bottom: 100%;
    left: auto;
    top: auto;
    margin: 0 0 8px 0;
    width: 280px;
    max-height: 300px;
    z-index: 999999;
}
.imvu-antibot-on {
    display: none;
}
.redesign #inputRow .imvu-antibot-button.active {
    border: 1px solid #39d353;
    background: #14381a;
    box-shadow: 0 0 6px rgba(57, 211, 83, 0.45);
    opacity: 1;
}
.redesign #inputRow .imvu-antibot-button.active .imvu-antibot-on {
    line-height: 23px;
}
.imvu-antibot-section-title {
    padding: 8px 10px 4px;
    color: #bbb;
    font-size: 11px;
    font-weight: bold;
    border-top: 1px solid #333;
}
.imvu-antibot-section-title:first-child {
    border-top: 0;
}
.imvu-antibot-note {
    padding: 6px 10px;
    color: #777;
    font-size: 10px;
    line-height: 1.4;
}
.imvu-antibot-popup-close {
    position: absolute;
    right: 6px;
    top: 4px;
    width: 22px;
    height: 22px;
    padding: 0;
    border: 0;
    background: transparent;
    color: #aaa;
    font-size: 16px;
    line-height: 20px;
    cursor: pointer;
}
.imvu-antibot-popup-close:hover {
    color: #fff;
}
.imvu-antibot-popup-title {
    padding-right: 28px;
}
"""

POPUP_LAYOUT_V3_CSS = """
/* IMVU antibot popup layout v3 — do not alter #text-chat layout */
#text-chat.imvu-antibot-root,
.imvu-antibot-anchor {
    position: static !important;
}
.imvu-antibot-popup {
    position: fixed !important;
    width: 280px !important;
    max-height: 300px !important;
    height: auto !important;
    left: auto;
    top: auto;
    right: auto;
    bottom: auto;
    margin: 0;
}
.imvu-antibot-popup[aria-hidden="true"] {
    display: none !important;
}
"""

POPUP_LAYOUT_V4_CSS = """
/* IMVU antibot popup layout v4 — fixed height, tabs always visible */
.imvu-antibot-popup {
    height: 220px !important;
    max-height: 220px !important;
    min-height: 220px !important;
    overflow: hidden !important;
}
.imvu-antibot-popup-head {
    overflow: hidden;
}
.imvu-antibot-popup-body {
    height: 142px !important;
    max-height: 142px !important;
    min-height: 142px !important;
    overflow-x: hidden !important;
    overflow-y: auto !important;
}
.imvu-antibot-whitelist-candidates,
.imvu-antibot-whitelist-trusted {
    max-height: none !important;
    overflow: visible !important;
}
.imvu-antibot-tabs {
    padding: 4px 8px 4px;
    position: relative;
    z-index: 2;
}
.imvu-antibot-section-title {
    padding: 4px 10px 2px;
    font-size: 10px;
}
.imvu-antibot-list li {
    padding: 4px 10px;
    padding-right: 56px;
}
.imvu-antibot-note,
.imvu-antibot-empty {
    padding: 4px 10px;
    font-size: 10px;
}
"""
