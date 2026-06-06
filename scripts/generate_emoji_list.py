"""Generate emoji_assets/js/emojiList.js from Unicode emoji-test.txt."""

import json
import os
import re
import sys
import urllib.request

EMOJI_TEST_URL = "https://unicode.org/Public/emoji/15.1/emoji-test.txt"
OUTPUT = os.path.join("emoji_assets", "js", "emojiList.js")

GROUP_MAP = {
    "Smileys & Emotion": ("smileys", "Smileys"),
    "People & Body": ("people", "People"),
    "Component": None,
    "Animals & Nature": ("nature", "Nature"),
    "Food & Drink": ("food", "Food"),
    "Travel & Places": ("travel", "Travel"),
    "Activities": ("activity", "Activity"),
    "Objects": ("objects", "Objects"),
    "Symbols": ("symbols", "Symbols"),
    "Flags": ("flags", "Flags"),
}

SKIP_SUBGROUPS = {
    "skin-tone",
    "hair-style",
    "component",
}

SKIP_NAME_PARTS = (
    " skin tone",
    " hair",
)


def codepoints_to_char(code_field):
    parts = code_field.strip().split()
    chars = []
    for part in parts:
        cp = int(part, 16)
        if cp <= 0xFFFF:
            chars.append(chr(cp))
        else:
            cp -= 0x10000
            chars.append(chr(0xD800 + (cp >> 10)))
            chars.append(chr(0xDC00 + (cp & 0x3FF)))
    return "".join(chars)


def js_ascii_string(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def js_char_string(text):
    out = ['"']
    i = 0
    while i < len(text):
        c = text[i]
        code = ord(c)
        if 0xD800 <= code <= 0xDBFF and i + 1 < len(text):
            c2 = text[i + 1]
            if 0xDC00 <= ord(c2) <= 0xDFFF:
                out.append("\\u%04X\\u%04X" % (code, ord(c2)))
                i += 2
                continue
        if code == 0x5C:
            out.append("\\\\")
        elif code == 0x22:
            out.append('\\"')
        elif code < 0x20 or code in (0x7F,):
            out.append("\\u%04X" % code)
        elif code <= 0xFFFF:
            out.append("\\u%04X" % code)
        else:
            out.append(c)
        i += 1
    out.append('"')
    return "".join(out)


def keywords_from_name(name):
    words = re.sub(r"[^a-z0-9 ]+", " ", name.lower()).split()
    stop = {"with", "and", "the", "for", "of", "in", "a", "an", "on", "to"}
    seen = []
    for word in words:
        if len(word) < 2 or word in stop:
            continue
        if word not in seen:
            seen.append(word)
    return " ".join(seen[:8])


def parse_emoji_test(text):
    group = ""
    subgroup = ""
    categories = {}
    order = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("# group:"):
            group = line.split(":", 1)[1].strip()
            continue
        if line.startswith("# subgroup:"):
            subgroup = line.split(":", 1)[1].strip()
            continue
        if "fully-qualified" not in line or line.startswith("#"):
            continue

        mapped = GROUP_MAP.get(group)
        if mapped is None:
            continue
        if subgroup in SKIP_SUBGROUPS:
            continue

        code_field, rest = line.split(";", 1)
        comment = rest.split("#", 1)[1]
        # Strip leading emoji glyph and version tag (e.g. "😀 E1.0 grinning face").
        name = re.sub(r"^\s*\S+\s+E\d+\.\d+\s+", "", comment).strip()
        if not name:
            name = comment.split("E")[0].strip()
            name = re.sub(r"^\S+\s+", "", name)
        if any(part in name for part in SKIP_NAME_PARTS):
            continue
        if subgroup == "country-flag" and "+" in name:
            continue

        cat_id, cat_label = mapped
        if cat_id not in categories:
            categories[cat_id] = {"id": cat_id, "label": cat_label, "emojis": []}
            order.append(cat_id)

        char = codepoints_to_char(code_field)
        categories[cat_id]["emojis"].append(
            {
                "c": char,
                "n": name,
                "k": keywords_from_name(name),
            }
        )

    return [categories[cat_id] for cat_id in order]


def render_js(categories):
    lines = [
        "/* IMVU emoji picker catalog — generated from Unicode emoji-test.txt */",
        "(function () {",
        "    if (window.IMVU_EMOJI_CATEGORIES) {",
        "        return;",
        "    }",
        "",
        "    window.IMVU_EMOJI_CATEGORIES = [",
    ]

    for cat in categories:
        lines.append("        {")
        lines.append("            id: '%s'," % cat["id"])
        lines.append("            label: '%s'," % cat["label"].replace("'", "\\'"))
        lines.append("            emojis: [")
        for entry in cat["emojis"]:
            lines.append(
                "                { c: %s, n: %s, k: %s },"
                % (
                    js_char_string(entry["c"]),
                    js_ascii_string(entry["n"]),
                    js_ascii_string(entry["k"]),
                )
            )
        lines.append("            ]")
        lines.append("        },")

    lines.append("    ];")
    lines.append("})();")
    lines.append("")
    return "\n".join(lines)


def main():
    print("Fetching %s ..." % EMOJI_TEST_URL, file=sys.stderr)
    with urllib.request.urlopen(EMOJI_TEST_URL, timeout=60) as resp:
        text = resp.read().decode("utf-8")

    categories = parse_emoji_test(text)
    total = sum(len(cat["emojis"]) for cat in categories)
    print("Parsed %s emojis in %s categories." % (total, len(categories)), file=sys.stderr)
    for cat in categories:
        print("  %s: %s" % (cat["label"], len(cat["emojis"])), file=sys.stderr)

    js = render_js(categories)
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(js)
    print("Wrote %s (%s bytes)" % (OUTPUT, len(js.encode("utf-8"))), file=sys.stderr)


if __name__ == "__main__":
    main()
