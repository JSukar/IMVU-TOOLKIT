import os
import zipfile

from imvu_toolkit.patches.emoji import constants as C
from imvu_toolkit.patches.emoji.patch import patch_content_jar, restore_jar

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def read_fixture(name):
    with open(os.path.join(FIXTURES, name), "r", encoding="utf-8") as f:
        return f.read()


def _write_minimal_jar(path):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        zout.writestr("tool/chat/ChatTool.js", read_fixture("ChatTool.js"))
        zout.writestr("tool/chat/index.html", read_fixture("chat_index.html"))
        zout.writestr("tool/chat/style.css", read_fixture("style.css"))
        zout.writestr("css/font.css", read_fixture("font.css"))


def test_patch_content_jar_round_trip(tmp_path):
    jar_path = tmp_path / "imvuContent.jar"
    _write_minimal_jar(jar_path)

    original_linkify = read_fixture("ChatTool.js")

    backup = patch_content_jar(str(jar_path))
    assert os.path.isfile(backup)

    with zipfile.ZipFile(jar_path, "r") as zin:
        js = zin.read("tool/chat/ChatTool.js").decode("utf-8")
        html = zin.read("tool/chat/index.html").decode("utf-8")
        assert C.LINKIFY_NEW in js
        assert "emojiPicker.js" in html
        assert "js/emojiDisplay.js" in set(zin.namelist())

    restore_backup = restore_jar(str(jar_path))
    assert restore_backup == backup

    with zipfile.ZipFile(jar_path, "r") as zin:
        js = zin.read("tool/chat/ChatTool.js").decode("utf-8")
        assert js == original_linkify
        assert C.LINKIFY_NEW not in js
