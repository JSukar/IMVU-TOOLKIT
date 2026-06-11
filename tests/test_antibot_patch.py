import os
import zipfile

from imvu_toolkit.patches.antibot import constants as C
from imvu_toolkit.patches.antibot.transforms import build_library_sources
from imvu_toolkit.zip_utils import rewrite_zip


def test_build_library_sources_contains_markers():
    entries = build_library_sources()
    assert C.ZIP_ANTIBOT_SOURCE in entries
    assert C.ZIP_MEET_SOURCE in entries
    assert C.ZIP_SESSION_DISPATCHER_SOURCE in entries
    assert C.ZIP_SESSIONWINDOW_SOURCE in entries
    assert C.ZIP_CHAT_TOOL_SOURCE in entries
    meet = entries[C.ZIP_MEET_SOURCE].decode("utf-8")
    assert C.PATCH_MARKER in meet
    assert "im.antibot.check_incoming_message" in meet
    assert "publish_protection_status" in meet
    dispatcher = entries[C.ZIP_SESSION_DISPATCHER_SOURCE].decode("utf-8")
    assert "im.antibot.should_boot_on_join" in dispatcher
    sessionwindow = entries[C.ZIP_SESSIONWINDOW_SOURCE].decode("utf-8")
    assert "SessionWindow.AntibotProtectionStatus" in sessionwindow
    chat_tool = entries[C.ZIP_CHAT_TOOL_SOURCE].decode("utf-8")
    assert "getAntibotWhitelist" in chat_tool
    assert "addAntibotWhitelistUser" in chat_tool
    assert "getAntibotProtectionStatus" in chat_tool
    compile(chat_tool, C.ZIP_CHAT_TOOL_SOURCE, "exec")
    for name, source in (
        (C.ZIP_CHAT_TOOL_SOURCE, chat_tool),
        (C.ZIP_SESSIONWINDOW_SOURCE, sessionwindow),
    ):
        assert "okay decompiling" not in source
        assert not any(line == "return" for line in source.splitlines())


def test_rewrite_zip_antibot_entries(tmp_path):
    library = tmp_path / "library.zip"
    with zipfile.ZipFile(library, "w") as zout:
        zout.writestr(C.ZIP_MEET_BYTECODE, b"old-meet-bytecode")
        zout.writestr(C.ZIP_SESSION_DISPATCHER_BYTECODE, b"old-dispatcher-bytecode")
        zout.writestr(C.ZIP_SESSIONWINDOW_BYTECODE, b"old-sessionwindow-bytecode")
        zout.writestr(C.ZIP_CHAT_TOOL_BYTECODE, b"old-chat-tool-bytecode")
        zout.writestr("im/common.pyo", b"keep")

    entries = build_library_sources()
    backup = rewrite_zip(
        str(library),
        C.BACKUP_PREFIX,
        skip_names=set(C.SKIP_BYTECODE),
        write_entries=entries,
    )
    assert os.path.exists(backup)
    with zipfile.ZipFile(library, "r") as zin:
        names = zin.namelist()
        assert C.ZIP_MEET_BYTECODE not in names
        assert C.ZIP_SESSION_DISPATCHER_BYTECODE not in names
        assert C.ZIP_SESSIONWINDOW_BYTECODE not in names
        assert C.ZIP_CHAT_TOOL_BYTECODE not in names
        assert C.ZIP_ANTIBOT_SOURCE in names
        assert zin.read(C.ZIP_ANTIBOT_SOURCE) == entries[C.ZIP_ANTIBOT_SOURCE]
        assert zin.read("im/common.pyo") == b"keep"
