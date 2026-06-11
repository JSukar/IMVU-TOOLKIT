"""Scan IMVU logs for JSON chatId vs IMQ queue /chat/<id> mismatches."""

import ast
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

IMQ_RE = re.compile(
    r"onImqMessage\(\['(\d+)', u'/chat/(\d+)', u'messages', '(.+)'\]\)"
)
FORGED_RE = re.compile(r"forged message detected")


def parse_json_blob(raw: str):
    """Parse the JSON string as it appears inside log single-quotes."""
    try:
        decoded = raw.encode("utf-8").decode("unicode_escape")
        return json.loads(decoded)
    except (UnicodeError, json.JSONDecodeError, ValueError):
        pass
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def classify_message(text):
    if not text:
        return "empty"
    if text.startswith("*"):
        return "protocol"
    if "vuarchives" in text.lower() or "findzu" in text.lower() or "findgu" in text.lower():
        return "promo"
    return "chat"


def analyze(path: Path):
    stats = {
        "total_imq_messages": 0,
        "json_parse_fail": 0,
        "missing_json_chatid": 0,
        "chatid_match": 0,
        "chatid_mismatch": 0,
        "forged_log_lines": 0,
    }
    mismatch_by_uid = defaultdict(list)
    match_by_uid = defaultdict(int)
    wrong_json_ids = defaultdict(int)
    mismatch_msg_kind = defaultdict(int)

    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if FORGED_RE.search(line):
                stats["forged_log_lines"] += 1

            match = IMQ_RE.search(line)
            if not match:
                continue

            uid, queue_chat, raw_json = match.group(1), match.group(2), match.group(3)
            stats["total_imq_messages"] += 1

            data = parse_json_blob(raw_json)
            if not isinstance(data, dict):
                stats["json_parse_fail"] += 1
                continue

            json_chat = data.get("chatId")
            if json_chat is None:
                stats["missing_json_chatid"] += 1
                continue

            try:
                queue_id = int(queue_chat)
                json_id = int(json_chat)
            except (TypeError, ValueError):
                continue

            message = data.get("message", "")
            kind = classify_message(message if isinstance(message, str) else "")

            if queue_id == json_id:
                stats["chatid_match"] += 1
                match_by_uid[uid] += 1
            else:
                stats["chatid_mismatch"] += 1
                mismatch_by_uid[uid].append(
                    (queue_id, json_id, kind, (message or "")[:100])
                )
                wrong_json_ids[json_id] += 1
                mismatch_msg_kind[kind] += 1

    return stats, mismatch_by_uid, match_by_uid, wrong_json_ids, mismatch_msg_kind


def main():
    paths = []
    if len(sys.argv) > 1:
        paths = [Path(p) for p in sys.argv[1:]]
    else:
        appdata = Path.home() / "AppData" / "Roaming" / "IMVU"
        paths = sorted(appdata.glob("IMVULog.log*"))
        repo = Path(__file__).resolve().parents[1]
        paths.extend(sorted((repo / "IMVU").glob("IMVULog.log*")))
        paths.extend(sorted((repo / "Logstoreverse").rglob("IMVULog.log*")))

    paths = [p for p in paths if p.is_file()]
    if not paths:
        print("No IMVULog files found.")
        return 1

    totals = defaultdict(int)
    all_mismatch = defaultdict(list)
    all_match = defaultdict(int)
    all_wrong_ids = defaultdict(int)
    all_kinds = defaultdict(int)

    for path in paths:
        stats, mismatch, match, wrong_ids, kinds = analyze(path)
        print(f"\n=== {path} ({path.stat().st_size // 1024} KB) ===")
        for key, value in sorted(stats.items()):
            print(f"  {key}: {value}")
            totals[key] += value
        for uid, rows in sorted(mismatch.items(), key=lambda item: -len(item[1]))[:8]:
            q, j, kind, sample = rows[0]
            print(
                f"  mismatch uid={uid} count={len(rows)} queue={q} json={j} "
                f"kind={kind} sample={sample!r}"
            )
        for uid, rows in mismatch.items():
            all_mismatch[uid].extend(rows)
        for uid, count in match.items():
            all_match[uid] += count
        for jid, count in wrong_ids.items():
            all_wrong_ids[jid] += count
        for kind, count in kinds.items():
            all_kinds[kind] += count

    print("\n=== Combined ===")
    for key, value in sorted(totals.items()):
        print(f"  {key}: {value}")

    if totals["chatid_match"]:
        pct = 100.0 * totals["chatid_mismatch"] / (
            totals["chatid_match"] + totals["chatid_mismatch"]
        )
        print(f"  mismatch_rate: {pct:.4f}%")

    print("\nMismatch message kinds:", dict(sorted(all_kinds.items())))
    print(
        "Top wrong JSON chatIds:",
        dict(sorted(all_wrong_ids.items(), key=lambda item: -item[1])[:10]),
    )

    mismatch_uids = set(all_mismatch)
    match_uids = set(all_match)
    both = mismatch_uids & match_uids
    only_mismatch = mismatch_uids - match_uids
    only_match = match_uids - mismatch_uids

    print(f"\nUIDs with any mismatch: {len(mismatch_uids)}")
    print(f"UIDs with only mismatches (never correct chatId): {len(only_mismatch)}")
    print(f"UIDs with both match and mismatch: {len(both)}")
    print(f"UIDs with only correct chatId: {len(only_match)}")

    if only_mismatch:
        print("\nOnly-mismatch UIDs (likely bots if exclusive):")
        for uid in sorted(only_mismatch, key=lambda u: -len(all_mismatch[u]))[:20]:
            rows = all_mismatch[uid]
            q, j, kind, sample = rows[0]
            print(
                f"  uid={uid} msgs={len(rows)} queue={q} json={j} "
                f"kinds={ {r[2] for r in rows} } sample={sample!r}"
            )

    if both:
        print("\nUIDs with BOTH correct and wrong chatId (would false-positive if naive):")
        for uid in sorted(both, key=lambda u: -len(all_mismatch[u]))[:10]:
            print(
                f"  uid={uid} mismatch={len(all_mismatch[uid])} match={all_match[uid]}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
