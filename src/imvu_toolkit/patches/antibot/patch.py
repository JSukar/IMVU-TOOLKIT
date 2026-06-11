"""Apply or restore the IMVU room antibot patch."""

import argparse
import os
import sys

from imvu_toolkit.imvu_process import ensure_imvu_closed, start_imvu
from imvu_toolkit.patches.antibot import constants as C
from imvu_toolkit.patches.antibot.transforms import (
    build_library_sources,
    patch_text_file,
    read_asset,
)
from imvu_toolkit.paths import DEFAULT_IMVU_DIR
from imvu_toolkit.zip_utils import restore_from_backup, rewrite_jar, rewrite_zip


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Patch IMVU to auto-boot VuArchives-style promo bots in rooms you own or mod.",
    )
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
    parser.add_argument(
        "--relaunch-imvu",
        action="store_true",
        help="Start IMVUClient.exe after a successful patch or restore.",
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
        if name in C.CHAT_HTML_FILES + C.CHAT_STYLE_FILES:
            return patch_text_file(data.decode("utf-8"), name).encode("utf-8")
        return None

    return rewrite_jar(jar_path, C.BACKUP_PREFIX, transform_entry, inject_entries=overrides)


def patch_library(library, write_entries):
    return rewrite_zip(
        library,
        C.BACKUP_PREFIX,
        skip_names=set(C.SKIP_BYTECODE),
        write_entries=write_entries,
    )


def restore_library(library):
    return restore_from_backup(library, C.BACKUP_PREFIX)


def restore_jar(jar_path):
    return restore_from_backup(jar_path, C.BACKUP_PREFIX)


def maybe_relaunch_imvu(imvu_dir, relaunch):
    if not relaunch:
        print("Restart IMVU to load the changes.")
        return 0
    ok, err = start_imvu(imvu_dir)
    if ok:
        print("IMVU restarted.")
        return 0
    print("Warning: %s" % err, file=sys.stderr)
    print("Restart IMVU manually to load the changes.")
    return 0


def main(argv=None):
    args = parse_args(argv)
    library = library_path(args)
    jar_path = content_jar_path(args)
    imvu_dir = os.path.dirname(library)

    for path in list(C.SOURCE_FILES.values()) + list(C.JAR_JS_ENTRIES.values()):
        if not os.path.exists(path):
            print("Missing %s" % path, file=sys.stderr)
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
        return maybe_relaunch_imvu(imvu_dir, args.relaunch_imvu)

    write_entries = build_library_sources()
    lib_backup = patch_library(library, write_entries)
    jar_backup = patch_content_jar(jar_path)
    print("Patched room antibot hooks in %s" % library)
    print("Library backup: %s" % lib_backup)
    print("Patched antibot protection UI in %s" % jar_path)
    print("Content backup: %s" % jar_backup)
    print(
        "When you own or mod a room, promo bots are booted automatically. "
        "Use the shield icon in chat to see protection status and boot log."
    )
    return maybe_relaunch_imvu(imvu_dir, args.relaunch_imvu)
