import os
import subprocess
import sys
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


def imvu_exe_path(imvu_dir):
    return os.path.join(os.path.abspath(imvu_dir), "IMVUClient.exe")


def start_imvu(imvu_dir):
    exe = imvu_exe_path(imvu_dir)
    if not os.path.isfile(exe):
        return False, "IMVUClient.exe not found: %s" % exe
    subprocess.Popen([exe], cwd=os.path.dirname(exe))
    return True, None


def wait_for_imvu_closed(imvu_dir, poll_interval=1.0, timeout=600):
    if not imvu_is_running(imvu_dir):
        return True, None

    print("")
    print("IMVU is still running.")
    print("Please close IMVU completely, then leave this window open.")
    print("The installer will continue automatically once IMVU has exited.")
    print("")

    deadline = time.time() + timeout if timeout else None
    dots = 0
    while True:
        if not imvu_is_running(imvu_dir):
            print("\nIMVU closed.")
            return True, None
        if deadline and time.time() >= deadline:
            return False, "Timed out after %d seconds waiting for IMVU to close." % timeout
        time.sleep(poll_interval)
        dots = (dots + 1) % 4
        message = "  Waiting for IMVU to close" + ("." * dots) + (" " * (3 - dots))
        sys.stdout.write("\r%s" % message)
        sys.stdout.flush()

    return False, "IMVUClient is still running."


def ensure_imvu_closed(imvu_dir, force, no_close_imvu):
    if not imvu_is_running(imvu_dir):
        return True, None

    if force:
        print("Warning: IMVU is running; --force continues anyway.", file=sys.stderr)
        return True, None

    if no_close_imvu:
        return False, "IMVUClient is running. Close IMVU manually and run again."

    return wait_for_imvu_closed(imvu_dir)
