import importlib.util
import os
import sys

from imvu_toolkit.paths import asset_path


def _load_antibot_module():
    path = asset_path("library_decompiled_structured", "im", "antibot.py")
    spec = importlib.util.spec_from_file_location("imvu_antibot_test", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["imvu_antibot_test"] = module
    spec.loader.exec_module(module)
    return module


def test_is_promo_message_detects_homoglyphs():
    antibot = _load_antibot_module()
    msg = u"Join vu\u0251r\u03f2hives.\u03bf\u03bfm/join discord.com/invite/h87FtAz6V8"
    assert antibot.is_promo_message(msg)


def test_is_promo_message_detects_zero_width_spacing():
    antibot = _load_antibot_module()
    msg = u"v\u200bu\u200ba\u200br\u200bc\u200bh\u200bi\u200bv\u200be\u200bs\u200b.\u200bc\u200bo\u200bm"
    assert antibot.is_promo_message(msg)


def test_is_promo_message_ignores_normal_chat():
    antibot = _load_antibot_module()
    assert not antibot.is_promo_message(u"hey welcome to my room")


def test_is_promo_message_flags_known_campaign_codes():
    antibot = _load_antibot_module()
    assert antibot.is_promo_message(u"discord.gg/sDKpD4knJd")
    assert antibot.is_promo_message(u"discord.com/invite/h87FtAz6V8")
    antibot = _load_antibot_module()
    assert not antibot.is_promo_message(u"join our discord.gg/mycommunity")
    assert not antibot.is_promo_message(u"discord.com/invite/abc123 is our server")
    assert not antibot.is_promo_message(u"I like vu models in the archives room")
    assert not antibot.is_promo_message(u"discord invite me later")


def test_should_boot_on_join_disabled():
    antibot = _load_antibot_module()

    class Info(object):
        isGuest = True
        avatarName = u"Guest_lakedark86"

    class Session(object):
        userId_ = 21517672

        def hasBootPrivileges(self, uid):
            return True

        def isRoomSession(self):
            return True

    assert not antibot.should_boot_on_join(Session(), 390288721, Info())


def test_whitelist_owner_bots():
    antibot = _load_antibot_module()
    for uid in (99815795, 386805690, 53421654):
        assert antibot.is_whitelisted(uid)
    assert not antibot.is_whitelisted(390288702)


def test_check_incoming_message_ignores_prejoin_protocol():
    antibot = _load_antibot_module()

    class Session(object):
        userId_ = 21517672

        def getParticipantUserIds(self):
            return [21517672, 386805690]

        def hasBootPrivileges(self, uid):
            return True

        def isRoomSession(self):
            return True

    session = Session()
    for msg in (
        u"*imvu:isPureUser",
        u"*msg SeatAssignment 3 390573580 4 0",
        u"*seat 3",
        u"*use 80 45773940",
    ):
        block, reason = antibot.check_incoming_message(
            session, 390573580, {"message": msg}
        )
        assert not block, msg
        assert reason is None, msg


def test_check_incoming_message_flags_prejoin_promo():
    antibot = _load_antibot_module()

    class Session(object):
        userId_ = 21517672

        def getParticipantUserIds(self):
            return [21517672]

        def hasBootPrivileges(self, uid):
            return True

        def isRoomSession(self):
            return True

    session = Session()
    block, reason = antibot.check_incoming_message(
        session,
        390288917,
        {"message": u"vuarchives.com discord.com/invite/h87FtAz6V8"},
    )
    assert block
    assert reason == "promo_message"


def test_whitelist_skips_boot():
    antibot = _load_antibot_module()

    class Session(object):
        userId_ = 21517672

        def canBoot(self, booter, bootee):
            return True

        def bootUser(self, userId):
            raise AssertionError("should not boot whitelisted user")

    session = Session()
    session.hasBootPrivileges = lambda uid: True
    session.isRoomSession = lambda: True
    assert not antibot.try_boot_spammer(session, 53421654, "promo_message")


def test_boot_log_and_protection_status():
    antibot = _load_antibot_module()

    class Session(object):
        userId_ = 21517672

        def hasBootPrivileges(self, uid):
            return True

        def isRoomSession(self):
            return True

    session = Session()
    antibot.clear_boot_log(session)
    assert antibot.is_protection_active(session)
    antibot.record_boot(session, 390288917, "promo_message", avatar_name="Guest_test123")
    log = antibot.get_boot_log(session)
    assert len(log) == 1
    assert log[0]["userId"] == 390288917
    assert log[0]["avatarName"] == "Guest_test123"
    assert log[0]["reason"] == "promo_message"
    status = antibot._protection_status_info(session)
    assert "whitelist" in status


def test_user_whitelist_add_remove(tmp_path, monkeypatch):
    antibot = _load_antibot_module()
    whitelist_path = tmp_path / "antibot_whitelist.json"
    monkeypatch.setattr(antibot, "_whitelist_file_path", lambda: str(whitelist_path))
    antibot._USER_WHITELIST = None

    ok, entries = antibot.add_to_whitelist(390288917, "Guest_test123")
    assert ok
    assert antibot.is_whitelisted(390288917)
    assert any(entry["userId"] == 390288917 for entry in entries)
    assert whitelist_path.exists()

    antibot._USER_WHITELIST = None
    assert antibot.is_whitelisted(390288917)

    ok, entries = antibot.remove_from_whitelist(390288917)
    assert ok
    antibot._USER_WHITELIST = None
    assert not antibot.is_whitelisted(390288917)
    assert not any(entry["userId"] == 390288917 and entry.get("removable") for entry in entries)


def test_builtin_whitelist_not_removable(tmp_path, monkeypatch):
    antibot = _load_antibot_module()
    monkeypatch.setattr(antibot, "_whitelist_file_path", lambda: str(tmp_path / "wl.json"))
    antibot._USER_WHITELIST = None
    ok, _entries = antibot.remove_from_whitelist(99815795)
    assert not ok
    assert antibot.is_whitelisted(99815795)
