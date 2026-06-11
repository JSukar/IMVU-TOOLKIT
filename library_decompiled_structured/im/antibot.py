# IMVU room antibot patch — auto-boot VuArchives-style promo bots in rooms you own or mod.
import json
import logging
import os
import re

try:
    unicode
except NameError:
    unicode = str

logger = logging.getLogger('imvu.' + __name__)

# Owner bots / trusted accounts — never auto-boot (built-in, not removable in UI).
_BUILTIN_WHITELIST_USER_IDS = frozenset((
    99815795,
    386805690,
    53421654,
))
_USER_WHITELIST = None

_BOOTED_USER_IDS = set()
_BOOT_LOG_BY_SESSION = {}


def _session_key(session):
    return id(session)


def clear_boot_log(session):
    _BOOT_LOG_BY_SESSION.pop(_session_key(session), None)


def get_boot_log(session):
    return list(_BOOT_LOG_BY_SESSION.get(_session_key(session), ()))


def record_boot(session, userId, reason, avatar_name=None):
    try:
        user_id = int(userId)
    except (TypeError, ValueError):
        return None
    if avatar_name is None:
        avatar_name = u'User %s' % user_id
    elif not isinstance(avatar_name, unicode):
        avatar_name = unicode(avatar_name)
    entry = {
        'userId': user_id,
        'reason': reason,
        'avatarName': avatar_name,
    }
    _BOOT_LOG_BY_SESSION.setdefault(_session_key(session), []).append(entry)
    return entry


def is_protection_active(session):
    return has_mod_boot_power(session)


def _whitelist_file_path():
    base = os.environ.get('APPDATA', '')
    if not base:
        return None
    return os.path.join(base, 'IMVUClient', 'antibot_whitelist.json')


def _load_user_whitelist():
    global _USER_WHITELIST
    if _USER_WHITELIST is not None:
        return _USER_WHITELIST
    _USER_WHITELIST = {}
    path = _whitelist_file_path()
    if path and os.path.exists(path):
        try:
            with open(path, 'r') as handle:
                data = json.load(handle)
            for entry in data.get('users', []):
                user_id = int(entry['userId'])
                avatar_name = entry.get('avatarName') or u'User %s' % user_id
                if not isinstance(avatar_name, unicode):
                    avatar_name = unicode(avatar_name)
                _USER_WHITELIST[user_id] = avatar_name
        except (IOError, ValueError, KeyError, TypeError) as err:
            logger.warning('IMVU antibot: could not load whitelist %r: %s', path, err)
    return _USER_WHITELIST


def _save_user_whitelist():
    path = _whitelist_file_path()
    if not path:
        return False
    try:
        directory = os.path.dirname(path)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        users = []
        for user_id, avatar_name in sorted(_load_user_whitelist().items()):
            users.append({'userId': user_id, 'avatarName': avatar_name})
        with open(path, 'w') as handle:
            json.dump({'users': users}, handle, indent=2)
        return True
    except (IOError, OSError) as err:
        logger.warning('IMVU antibot: could not save whitelist: %s', err)
        return False


def get_whitelist_display():
    entries = []
    seen = set()
    user_whitelist = _load_user_whitelist()
    for user_id in sorted(_BUILTIN_WHITELIST_USER_IDS):
        entries.append({
            'userId': user_id,
            'avatarName': user_whitelist.get(user_id) or u'User %s' % user_id,
            'removable': False,
            'builtin': True,
        })
        seen.add(user_id)
    for user_id, avatar_name in sorted(user_whitelist.items()):
        if user_id in seen:
            continue
        entries.append({
            'userId': user_id,
            'avatarName': avatar_name,
            'removable': True,
            'builtin': False,
        })
    return entries


def add_to_whitelist(userId, avatar_name=None):
    try:
        user_id = int(userId)
    except (TypeError, ValueError):
        return False, get_whitelist_display()
    if user_id in _BUILTIN_WHITELIST_USER_IDS:
        return True, get_whitelist_display()
    user_whitelist = _load_user_whitelist()
    if avatar_name is None:
        avatar_name = user_whitelist.get(user_id) or u'User %s' % user_id
    elif not isinstance(avatar_name, unicode):
        avatar_name = unicode(avatar_name)
    user_whitelist[user_id] = avatar_name
    _save_user_whitelist()
    logger.info('IMVU antibot: whitelisted user %r (%s)', user_id, avatar_name)
    return True, get_whitelist_display()


def remove_from_whitelist(userId):
    try:
        user_id = int(userId)
    except (TypeError, ValueError):
        return False, get_whitelist_display()
    if user_id in _BUILTIN_WHITELIST_USER_IDS:
        return False, get_whitelist_display()
    user_whitelist = _load_user_whitelist()
    if user_id not in user_whitelist:
        return False, get_whitelist_display()
    del user_whitelist[user_id]
    _save_user_whitelist()
    logger.info('IMVU antibot: removed user %r from whitelist', user_id)
    return True, get_whitelist_display()


def _protection_status_info(session):
    return {
        'active': is_protection_active(session),
        'boots': get_boot_log(session),
        'whitelist': get_whitelist_display(),
    }


def publish_protection_status(session, event_bus):
    if not event_bus:
        return
    event_bus.fire(session, 'AntibotProtectionStatus', _protection_status_info(session))


def publish_boot(session, event_bus, userId, reason, avatar_name=None):
    entry = record_boot(session, userId, reason, avatar_name=avatar_name)
    if not entry or not event_bus:
        return entry
    info = dict(entry)
    info['boots'] = get_boot_log(session)
    event_bus.fire(session, 'AntibotBooted', info)
    publish_protection_status(session, event_bus)
    return entry


def is_whitelisted(userId):
    try:
        user_id = int(userId)
    except (TypeError, ValueError):
        return False
    if user_id in _BUILTIN_WHITELIST_USER_IDS:
        return True
    return user_id in _load_user_whitelist()

_ZERO_WIDTH = (
    u'\u200b',
    u'\u200c',
    u'\u200d',
    u'\ufeff',
    u'\u2060',
)

_HOMOGLYPHS = (
    (u'\u0430', 'a'),
    (u'\u0251', 'a'),
    (u'\u03b1', 'a'),
    (u'\u0435', 'e'),
    (u'\u03bf', 'o'),
    (u'\u043e', 'o'),
    (u'\u0441', 'c'),
    (u'\u03f2', 'c'),
    (u'\u0456', 'i'),
    (u'\u0131', 'i'),
    (u'\u0440', 'p'),
    (u'\u03c1', 'p'),
    (u'\u057d', 's'),
    (u'\u0570', 'h'),
    (u'\u0578', 'o'),
    (u'\u057c', 'r'),
    (u'\u0576', 'n'),
)

_PROMO_MARKERS = (
    'vuarchives.com',
    'h87ftaz6v8',
    'sdkpd4knjd',
)


def _normalize_promo_text(text):
    if text is None:
        return u''
    if not isinstance(text, unicode):
        text = unicode(text)
    normalized = text.lower()
    for ch in _ZERO_WIDTH:
        normalized = normalized.replace(ch, u'')
    for src, dst in _HOMOGLYPHS:
        normalized = normalized.replace(src, dst)
    return normalized


def is_promo_message(text):
    normalized = _normalize_promo_text(text)
    if not normalized:
        return False
    for marker in _PROMO_MARKERS:
        if marker in normalized:
            return True
    # VuArchives brand as one word (not separate "vu" + "archives" elsewhere in chat).
    if 'vuarchives' in normalized:
        return True
    return False


def has_mod_boot_power(session):
    if not getattr(session, 'isRoomSession', lambda: False)():
        return False
    has_priv = getattr(session, 'hasBootPrivileges', None)
    if not has_priv:
        return False
    return bool(has_priv(session.userId_))


def try_boot_spammer(session, userId, reason, avatar_name=None, event_bus=None):
    if userId in (0, session.userId_):
        return False
    if is_whitelisted(userId):
        return False
    if userId in _BOOTED_USER_IDS:
        return True
    if not has_mod_boot_power(session):
        return False
    if not session.canBoot(session.userId_, userId):
        return False
    boot = getattr(session, 'bootUser', None)
    if not boot:
        return False
    _BOOTED_USER_IDS.add(userId)
    boot(userId)
    logger.info('IMVU antibot: booted user %r (%s)', userId, reason)
    publish_boot(session, event_bus, userId, reason, avatar_name=avatar_name)
    return True


def check_incoming_message(session, from_id, message_dict):
    if not has_mod_boot_power(session):
        return False, None
    if is_whitelisted(from_id):
        return False, None
    message = message_dict.get('message', '')
    if is_promo_message(message):
        return True, 'promo_message'
    return False, None


def should_boot_on_join(session, userId, avatarInfo):
    # Join-time guest-name boot removed: real Guest_* accounts false-positive too often.
    # Boot only after an actual promo message (see check_incoming_message / meet.py).
    return False
