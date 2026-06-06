import glob
import os
import shutil
import tempfile
import time
import zipfile


def newest_backup(target, prefix):
    matches = sorted(glob.glob(target + prefix + "*"))
    return matches[-1] if matches else None


def restore_from_backup(target, prefix):
    backup = newest_backup(target, prefix)
    if not backup:
        raise RuntimeError("No backup found for %s (prefix %s)" % (target, prefix))
    shutil.copy2(backup, target)
    return backup


def rewrite_zip(source_path, backup_prefix, skip_names, write_entries):
    """Rewrite a zip, skipping skip_names and writing write_entries instead."""
    backup = "%s%s%s" % (source_path, backup_prefix, time.strftime("%Y%m%d-%H%M%S"))
    shutil.copy2(source_path, backup)

    fd, temp_path = tempfile.mkstemp(
        prefix=os.path.basename(source_path) + ".",
        suffix=".zip",
        dir=os.path.dirname(os.path.abspath(source_path)),
    )
    os.close(fd)

    try:
        with zipfile.ZipFile(source_path, "r") as zin:
            payloads = []
            for info in zin.infolist():
                if info.filename in skip_names or info.filename in write_entries:
                    continue
                payloads.append((info, zin.read(info.filename)))

        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for info, data in payloads:
                zout.writestr(info, data)
            for name, data in write_entries.items():
                info = zipfile.ZipInfo(name, time.localtime(time.time())[:6])
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                zout.writestr(info, data)

        os.chmod(source_path, 0o666)
        os.replace(temp_path, source_path)
        return backup
    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise


def rewrite_jar(source_path, backup_prefix, transform_entry):
    """Rewrite jar entries via transform_entry(name, data) -> new data or None to keep."""
    backup = "%s%s%s" % (source_path, backup_prefix, time.strftime("%Y%m%d-%H%M%S"))
    shutil.copy2(source_path, backup)

    fd, temp_path = tempfile.mkstemp(
        prefix=os.path.basename(source_path) + ".",
        suffix=".jar",
        dir=os.path.dirname(os.path.abspath(source_path)),
    )
    os.close(fd)

    overrides = {}
    try:
        with zipfile.ZipFile(source_path, "r") as zin:
            for info in zin.infolist():
                name = info.filename
                data = zin.read(name)
                transformed = transform_entry(name, data)
                if transformed is not None:
                    overrides[name] = transformed

            payloads = []
            for info in zin.infolist():
                if info.filename in overrides:
                    continue
                payloads.append((info, zin.read(info.filename)))

        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for info, data in payloads:
                zout.writestr(info, data)
            for name, data in overrides.items():
                info = zipfile.ZipInfo(name, time.localtime(time.time())[:6])
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                zout.writestr(info, data)

        os.chmod(source_path, 0o666)
        os.replace(temp_path, source_path)
        return backup
    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise
