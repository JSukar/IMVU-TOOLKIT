"""Analyze IMVU client logs for VuArchives bot behavior."""
import glob
import os
import re
from collections import Counter, defaultdict

LOG_DIR = os.path.join(os.environ.get("APPDATA", ""), "IMVU")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROMO_RE = re.compile(
    r"vu[\u0251\u0430a][r\u0279\u043f][\u03f2c]hives|h87ftaz6v8|sdkpd4knjd|discord\.com/invite",
    re.I,
)


def log_files():
    paths = glob.glob(os.path.join(LOG_DIR, "IMVULog.log*"))
    for pattern in (
        os.path.join(REPO, "IMVU", "IMVULog.log*"),
        os.path.join(REPO, "Logstoreverse", "**", "IMVULog.log*"),
    ):
        paths.extend(glob.glob(pattern, recursive=True))
    return sorted(set(paths))


def parse_line(line):
    m = re.match(r"^(\d+\.\d+)\s", line)
    return float(m.group(1)) if m else None


def classify(path, lineno, ts, line):
    if "IMVU antibot: booted user" in line:
        m = re.search(r"booted user (\d+) \(([^)]+)\)", line)
        if m:
            return ("antibot_boot", m.group(1), m.group(2))
    if "boot user" in line and "antibot" not in line.lower():
        m = re.search(r"boot user (\d+)", line)
        if m:
            return ("manual_boot", m.group(1), "")
    if not PROMO_RE.search(line):
        return None
    if "onImqMessage" in line:
        m = re.search(r"\['(\d+)'", line)
        return ("promo_imq", m.group(1) if m else "", "")
    if "Deferring message" in line:
        m = re.search(r"'from_id': (\d+)", line)
        return ("defer_promo", m.group(1) if m else "", "")
    if "notifyNewMessage" in line:
        m = re.search(r"notifyNewMessage called for (\d+)", line)
        return ("promo_chat_ui", m.group(1) if m else "", "")
    if "Ignoring message" in line:
        m = re.search(r"'from_id': (\d+)", line)
        return ("ignored_promo", m.group(1) if m else "", "")
    return None


def session_chat(line):
    m = re.search(r"chat (\d+)", line)
    return m.group(1) if m else ""


def gather_promo_sequences(path):
    """Build per-UID promo timelines from one log file."""
    by_uid = defaultdict(list)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for lineno, line in enumerate(f, 1):
            ts = parse_line(line)
            hit = classify(path, lineno, ts, line)
            if not hit:
                continue
            kind, uid, extra = hit
            if not uid:
                continue
            by_uid[uid].append(
                {
                    "ts": ts,
                    "lineno": lineno,
                    "kind": kind,
                    "extra": extra,
                    "chat": session_chat(line),
                }
            )
    return by_uid


def first_message_for_uid(path, uid):
    """First non-promo defer/onImq for UID to see join protocol."""
    patterns = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for lineno, line in enumerate(f, 1):
            if uid not in line:
                continue
            ts = parse_line(line)
            if "onImqMessage" in line or "Deferring message" in line:
                patterns.append((ts, lineno, line.strip()[:220]))
            if "participantAdded called for %s" % uid in line:
                patterns.append((ts, lineno, "participantAdded"))
            if "NEW PARTICIPANT" in line and uid in line:
                patterns.append((ts, lineno, "NEW PARTICIPANT UI"))
            if "participantLeft called for %s" % uid in line:
                patterns.append((ts, lineno, "participantLeft"))
    return patterns


def main():
    files = log_files()
    print("Log files:", len(files))
    for p in files:
        print(" ", p)

    all_events = []
    for path in files:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for lineno, line in enumerate(f, 1):
                ts = parse_line(line)
                hit = classify(path, lineno, ts, line)
                if hit:
                    kind, uid, extra = hit
                    all_events.append((path, lineno, ts, kind, uid, extra))

    print("\n=== EVENT COUNTS (all logs) ===")
    for kind, count in Counter(e[3] for e in all_events).most_common():
        print("  %s: %d" % (kind, count))

    print("\n=== ANTIBOT BOOTS (live log) ===")
    live = os.path.join(LOG_DIR, "IMVULog.log")
    for e in all_events:
        if e[0] == live and e[3] == "antibot_boot":
            print("  L%s ts=%s uid=%s reason=%s" % (e[1], e[2], e[4], e[5]))

    print("\n=== PROMO BOT TIMELINES (live log) ===")
    seqs = gather_promo_sequences(live)
    for uid in sorted(seqs, key=lambda u: seqs[u][0]["ts"] or 0):
        evs = seqs[uid]
        chat = evs[0].get("chat", "")
        chain = " -> ".join(e["kind"] for e in evs)
        t0 = evs[0]["ts"]
        t1 = evs[-1]["ts"]
        dwell = ("%.3fs" % (t1 - t0)) if t0 and t1 and len(evs) > 1 else "n/a"
        print("  UID %s chat=%s dwell=%s" % (uid, chat, dwell))
        print("    %s" % chain)
        for e in evs:
            print("      L%s %.3f %s" % (e["lineno"], e["ts"] or 0, e["kind"]))

    print("\n=== PATTERN OUTCOMES (live promo UIDs) ===")
    for uid, evs in seqs.items():
        kinds = {e["kind"] for e in evs}
        if "promo_chat_ui" in kinds:
            outcome = "C: ad shown in chat"
        elif "ignored_promo" in kinds:
            outcome = "D: ignored (never joined)"
        elif "antibot_boot" in kinds or any(
            e[3] == "manual_boot" and e[4] == uid for e in all_events if e[0] == live
        ):
            outcome = "E: booted"
        elif "defer_promo" in kinds:
            outcome = "A: deferred (likely joined if no ignore)"
        else:
            outcome = "?: unknown"
        manual = any(e[3] == "manual_boot" and e[4] == uid for e in all_events)
        antibot = any(e[3] == "antibot_boot" and e[4] == uid for e in all_events)
        print("  %s -> %s manual=%s antibot=%s" % (uid, outcome, manual, antibot))

    print("\n=== PREJOIN BOOTS — CONTEXT (possible false positives) ===")
    for e in all_events:
        if e[0] != live or e[3] != "antibot_boot" or e[5] != "prejoin_room_chat":
            continue
        uid = e[4]
        ctx = first_message_for_uid(live, uid)[:8]
        print("  UID %s (boot L%s):" % (uid, e[1]))
        for ts, ln, snippet in ctx:
            print("    L%s %.3f %s" % (ln, ts or 0, snippet[:120]))


if __name__ == "__main__":
    main()
