import os
import subprocess
import sys
import time


def _hidden_subprocess_kwargs():
    if sys.platform != "win32":
        return {}
    kwargs = {"creationflags": subprocess.CREATE_NO_WINDOW}
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    kwargs["startupinfo"] = startupinfo
    return kwargs


def _win_process_image_path(pid):
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.windll.kernel32
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return None
    try:
        size = wintypes.DWORD(32768)
        buffer = ctypes.create_unicode_buffer(size.value)
        if kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            return buffer.value
    finally:
        kernel32.CloseHandle(handle)
    return None


def _win_imvu_client_processes(imvu_dir):
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.windll.kernel32
    imvu_dir = os.path.abspath(imvu_dir).lower()
    processes = []

    TH32CS_SNAPPROCESS = 0x00000002

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", wintypes.WCHAR * 260),
        ]

    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot == ctypes.c_void_p(-1).value:
        return None

    entry = PROCESSENTRY32W()
    entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)

    try:
        if not kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
            return processes
        while True:
            if entry.szExeFile.lower() == "imvuclient.exe":
                pid = entry.th32ProcessID
                path = _win_process_image_path(pid)
                if path and os.path.dirname(path).lower() == imvu_dir:
                    processes.append((pid, path))
            if not kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
                break
    finally:
        kernel32.CloseHandle(snapshot)

    return processes


def _powershell_imvu_client_processes(imvu_dir):
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
            **_hidden_subprocess_kwargs(),
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


def imvu_client_processes(imvu_dir):
    if sys.platform == "win32":
        processes = _win_imvu_client_processes(imvu_dir)
        if processes is not None:
            return processes
    return _powershell_imvu_client_processes(imvu_dir)


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
    last_gui_status = 0.0
    use_tty_progress = getattr(sys.stdout, "isatty", lambda: False)()
    while True:
        if not imvu_is_running(imvu_dir):
            if use_tty_progress:
                print("")
            print("IMVU closed.")
            return True, None
        if deadline and time.time() >= deadline:
            return False, "Timed out after %d seconds waiting for IMVU to close." % timeout
        time.sleep(poll_interval)
        dots = (dots + 1) % 4
        message = "  Waiting for IMVU to close" + ("." * dots) + (" " * (3 - dots))
        if use_tty_progress:
            sys.stdout.write("\r%s" % message)
            sys.stdout.flush()
        else:
            now = time.time()
            if now - last_gui_status >= 5.0:
                print(message.strip())
                last_gui_status = now

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
