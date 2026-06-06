import os
import subprocess
import time


def imvu_client_processes(imvu_dir):
    imvu_dir = os.path.abspath(imvu_dir).lower()
    processes = []
    try:
        output = subprocess.check_output(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-Process IMVUClient -ErrorAction SilentlyContinue | "
                "ForEach-Object { $_.Id.ToString() + '|' + $_.Path }",
            ],
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except Exception:
        return processes
    for line in output.splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        pid_text, path = line.split("|", 1)
        path = path.strip()
        if path and os.path.dirname(path).lower() == imvu_dir:
            try:
                processes.append((int(pid_text), path))
            except ValueError:
                continue
    return processes


def imvu_is_running(imvu_dir):
    return bool(imvu_client_processes(imvu_dir))


def close_imvu(imvu_dir, timeout=20):
    processes = imvu_client_processes(imvu_dir)
    if not processes:
        return True, None

    for pid, _path in processes:
        print("Closing IMVUClient (PID %d)..." % pid)
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    deadline = time.time() + timeout
    while time.time() < deadline:
        if not imvu_is_running(imvu_dir):
            return True, None
        time.sleep(0.5)

    return False, "IMVUClient is still running. Close it manually and try again."


def ensure_imvu_closed(imvu_dir, force, no_close_imvu):
    if not imvu_is_running(imvu_dir):
        return True, None

    if force:
        return True, None

    if no_close_imvu:
        return False, "IMVUClient is running. Close IMVU or rerun without --no-close-imvu."

    print("IMVU is running. Closing it automatically...")
    ok, err = close_imvu(imvu_dir)
    if ok:
        print("IMVU closed.")
        return True, None
    return False, err
