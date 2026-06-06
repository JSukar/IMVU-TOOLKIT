"""Apply or restore the IMVU emoji patch."""

import argparse
import os
import sys

from imvu_toolkit.imvu_process import ensure_imvu_closed
from imvu_toolkit.patches.emoji import constants as C
from imvu_toolkit.patches.emoji.transforms import (
    build_common_source,
    patch_font_css,
    patch_text_file,
    read_asset,
)
from imvu_toolkit.paths import DEFAULT_IMVU_DIR
from imvu_toolkit.zip_utils import restore_from_backup, rewrite_jar, rewrite_zip


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Patch IMVU chat emoji rendering.")
    parser.add_argument("--imvu-dir", default=DEFAULT_IMVU_DIR)
    parser.add_argument("--library", help="Path to library.zip (overrides --imvu-dir).")
    parser.add_argument("--content-jar", help="Path to imvuContent.jar (overrides --imvu-dir).")
    parser.add_argument("--restore", action="store_true")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Patch even if IMVU appears to be running.",
    )
    parser.add_argument(
        "--no-close-imvu",
        action="store_true",
        help="Do not automatically close IMVU before patching.",
    )
    return parser.parse_args(argv)


def library_path(args):
    if args.library:
        return os.path.abspath(args.library)
    return os.path.join(args.imvu_dir, "library.zip")


def content_jar_path(args):
    if args.content_jar:
        return os.path.abspath(args.content_jar)
    return os.path.join(args.imvu_dir, "ui", "chrome", "imvuContent.jar")


def patch_content_jar(jar_path):
    overrides = {}
    for jar_entry, source_path in C.JAR_JS_ENTRIES.items():
        overrides[jar_entry] = read_asset(source_path)

    def transform_entry(name, data):
        if name in overrides:
            return overrides[name]
        if name == C.FONT_ENTRY:
            return patch_font_css(data.decode("utf-8")).encode("utf-8")
        if name in C.CHAT_JS_FILES + C.CHAT_HTML_FILES + C.CHAT_STYLE_FILES:
            return patch_text_file(data.decode("utf-8"), name).encode("utf-8")
        return None

    return rewrite_jar(jar_path, C.BACKUP_PREFIX, transform_entry)


def patch_library(library, patched_source):
    return rewrite_zip(
        library,
        C.BACKUP_PREFIX,
        skip_names={C.ZIP_COMMON_BYTECODE, C.ZIP_COMMON_SOURCE},
        write_entries={C.ZIP_COMMON_SOURCE: patched_source},
    )


def restore_library(library):
    return restore_from_backup(library, C.BACKUP_PREFIX)


def restore_jar(jar_path):
    return restore_from_backup(jar_path, C.BACKUP_PREFIX)


def main(argv=None):
    args = parse_args(argv)
    library = library_path(args)
    jar_path = content_jar_path(args)
    imvu_dir = os.path.dirname(library)

    for path in C.JAR_JS_ENTRIES.values():
        if path == C.COMMON_SOURCE:
            continue
        if not os.path.exists(path):
            print("Missing %s" % path, file=sys.stderr)
            return 1
    if not os.path.exists(C.COMMON_SOURCE):
        print("Missing %s" % C.COMMON_SOURCE, file=sys.stderr)
        return 1

    if not os.path.exists(library):
        print("Missing library.zip: %s" % library, file=sys.stderr)
        return 1
    if not os.path.exists(jar_path):
        print("Missing imvuContent.jar: %s" % jar_path, file=sys.stderr)
        return 1

    ok, err = ensure_imvu_closed(imvu_dir, args.force, args.no_close_imvu)
    if not ok:
        print(err, file=sys.stderr)
        return 2

    if args.restore:
        lib_backup = restore_library(library)
        jar_backup = restore_jar(jar_path)
        print("Restored %s from %s" % (library, lib_backup))
        print("Restored %s from %s" % (jar_path, jar_backup))
        return 0

    common_source = build_common_source()
    lib_backup = patch_library(library, common_source)
    jar_backup = patch_content_jar(jar_path)
    print("Patched chat message UTF-8 decoding in %s" % library)
    print("Library backup: %s" % lib_backup)
    print("Patched Twemoji chat rendering + emoji picker in %s" % jar_path)
    print("Content backup: %s" % jar_backup)
    print("Restart IMVU to load the changes.")
    print("Note: emoji images load from jsDelivr (internet required in chat).")
    return 0
