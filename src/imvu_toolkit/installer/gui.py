"""Tkinter GUI for the IMVU emoji patch installer."""

from __future__ import annotations

import os
import queue
import sys
import threading
import tkinter as tk
import webbrowser
from tkinter import messagebox, scrolledtext, ttk

from imvu_toolkit import __version__
from imvu_toolkit.installer.runner import ensure_import_path, run_patch
from imvu_toolkit.paths import asset_path

REPO_URL = "https://github.com/JSukar/IMVU-TOOLKIT"

BG = "#1a1a1a"
PANEL = "#222222"
BORDER = "#444444"
TEXT = "#dddddd"
MUTED = "#929292"
ACCENT = "#6eb5ff"
SUCCESS = "#7dcea0"
ERROR = "#e07070"
GOLD = "#f5c542"


class InstallerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.log_queue: queue.Queue[str | None] = queue.Queue()
        self.worker: threading.Thread | None = None
        self.running = False
        self._logo_photo = None

        root.title("IMVU Emoji Patch Installer")
        root.configure(bg=BG)
        root.minsize(480, 440)
        root.geometry("540x500")

        self._set_window_icon()
        self._build_ui()
        self._poll_log_queue()

    def _set_window_icon(self) -> None:
        ico_path = asset_path("assets", "imvu-toolkit-logo.ico")
        if os.path.isfile(ico_path):
            try:
                self.root.iconbitmap(ico_path)
            except tk.TclError:
                pass

    def _build_ui(self) -> None:
        outer = tk.Frame(self.root, bg=BG, padx=16, pady=16)
        outer.pack(fill=tk.BOTH, expand=True)

        hero = tk.Frame(outer, bg=BG)
        hero.pack(fill=tk.X, pady=(0, 14))

        logo_wrap = tk.Frame(hero, bg=BG)
        logo_wrap.pack(side=tk.LEFT, padx=(0, 16))

        self._logo_photo = self._load_logo_photo(max_width=200)
        if self._logo_photo is not None:
            logo_label = tk.Label(logo_wrap, image=self._logo_photo, bg=BG, borderwidth=0)
            logo_label.pack()

        header = tk.Frame(hero, bg=BG)
        header.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        title = tk.Label(
            header,
            text="Emoji Patch Installer",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 15, "bold"),
            anchor=tk.W,
            justify=tk.LEFT,
        )
        title.pack(anchor=tk.W)

        subtitle = tk.Label(
            header,
            text="v%s  ·  Twemoji chat rendering + emoji picker" % __version__,
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
            anchor=tk.W,
            justify=tk.LEFT,
        )
        subtitle.pack(anchor=tk.W, pady=(6, 0))

        link = tk.Label(
            header,
            text=REPO_URL,
            bg=BG,
            fg=ACCENT,
            font=("Segoe UI", 9, "underline"),
            cursor="hand2",
            anchor=tk.W,
            justify=tk.LEFT,
        )
        link.pack(anchor=tk.W, pady=(4, 0))
        link.bind("<Button-1>", lambda _e: webbrowser.open(REPO_URL))

        btn_row = tk.Frame(outer, bg=BG)
        btn_row.pack(fill=tk.X, pady=(0, 10))

        self.install_btn = tk.Button(
            btn_row,
            text="Install Emoji Patch",
            command=lambda: self.start_job(restore=False),
            bg=PANEL,
            fg=TEXT,
            activebackground="#333333",
            activeforeground=TEXT,
            relief=tk.FLAT,
            padx=14,
            pady=8,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
        )
        self.install_btn.pack(side=tk.LEFT)

        self.restore_btn = tk.Button(
            btn_row,
            text="Restore Original",
            command=lambda: self.start_job(restore=True),
            bg=PANEL,
            fg=MUTED,
            activebackground="#333333",
            activeforeground=TEXT,
            relief=tk.FLAT,
            padx=14,
            pady=8,
            font=("Segoe UI", 10),
            cursor="hand2",
        )
        self.restore_btn.pack(side=tk.LEFT, padx=(8, 0))

        hint = tk.Label(
            outer,
            text="If IMVU is open, close it when prompted. The installer waits, patches, then relaunches IMVU.",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
            wraplength=480,
            justify=tk.LEFT,
        )
        hint.pack(fill=tk.X, pady=(0, 10))

        log_frame = tk.Frame(outer, bg=BORDER, padx=1, pady=1)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log = scrolledtext.ScrolledText(
            log_frame,
            bg="#111111",
            fg=TEXT,
            insertbackground=TEXT,
            relief=tk.FLAT,
            font=("Consolas", 9),
            wrap=tk.WORD,
            state=tk.DISABLED,
        )
        self.log.pack(fill=tk.BOTH, expand=True)

        footer = tk.Frame(outer, bg=BG)
        footer.pack(fill=tk.X, pady=(10, 0))

        self.status = tk.Label(
            footer,
            text="Ready.",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
            anchor=tk.W,
        )
        self.status.pack(side=tk.LEFT, fill=tk.X, expand=True)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Installer.Horizontal.TProgressbar",
            troughcolor="#111111",
            background=GOLD,
            bordercolor=BORDER,
            lightcolor=GOLD,
            darkcolor=GOLD,
        )
        self.progress = ttk.Progressbar(
            footer,
            mode="indeterminate",
            length=120,
            style="Installer.Horizontal.TProgressbar",
        )
        self.progress.pack(side=tk.RIGHT)

    def _load_logo_photo(self, max_width: int = 200):
        logo_path = asset_path("assets", "imvu-toolkit-logo.png")
        if not os.path.isfile(logo_path):
            return None
        try:
            from PIL import Image, ImageTk

            pil = Image.open(logo_path).convert("RGBA")
            width, height = pil.size
            if width > max_width:
                new_height = max(1, int(height * max_width / width))
                pil = pil.resize((max_width, new_height), Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(pil, master=self.root)
        except ImportError:
            pass
        except OSError:
            return None
        try:
            img = tk.PhotoImage(file=logo_path, master=self.root)
            factor = max(1, img.width() // max_width)
            return img.subsample(factor, factor)
        except tk.TclError:
            return None

    def append_log(self, text: str) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, text)
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def set_status(self, text: str, tone: str = "muted") -> None:
        colors = {"muted": MUTED, "ok": SUCCESS, "err": ERROR, "active": GOLD}
        self.status.configure(text=text, fg=colors.get(tone, MUTED))

    def set_busy(self, busy: bool) -> None:
        state = tk.DISABLED if busy else tk.NORMAL
        self.install_btn.configure(state=state)
        self.restore_btn.configure(state=state)
        if busy:
            self.progress.start(12)
        else:
            self.progress.stop()

    def start_job(self, restore: bool) -> None:
        if self.running:
            return
        if restore and not messagebox.askyesno(
            "Restore original files?",
            "This removes the emoji patch and restores library.zip / imvuContent.jar backups.\n\nContinue?",
            icon="warning",
        ):
            return

        self.running = True
        self.set_busy(True)
        self.log.configure(state=tk.NORMAL)
        self.log.delete("1.0", tk.END)
        self.log.configure(state=tk.DISABLED)
        self.set_status("Running...", tone="active")
        self.append_log("Mode: %s\n" % ("RESTORE" if restore else "INSTALL"))
        self.append_log("-" * 48 + "\n")

        self.worker = threading.Thread(
            target=self._worker,
            args=(restore,),
            daemon=True,
        )
        self.worker.start()

    def _worker(self, restore: bool) -> None:
        stdout = sys.stdout
        stderr = sys.stderr
        code = 1
        try:
            sys.stdout = _QueueStream(self.log_queue)
            sys.stderr = _QueueStream(self.log_queue)
            code = run_patch(restore=restore)
        except Exception as exc:
            self.log_queue.put("Error: %s\n" % exc)
            code = 1
        finally:
            sys.stdout = stdout
            sys.stderr = stderr
            self.log_queue.put(None)
            self.root.after(0, lambda: self._finish(code, restore))

    def _finish(self, code: int, restore: bool) -> None:
        self.running = False
        self.set_busy(False)
        self.append_log("-" * 48 + "\n")
        if code == 0:
            msg = (
                "Restore complete."
                if restore
                else "Install complete. Click the smiley button beside Send in chat."
            )
            self.append_log(msg + "\n")
            self.set_status(msg, tone="ok")
            messagebox.showinfo("Done", msg)
        elif code == 2:
            msg = "IMVU did not close in time. Close it completely and try again."
            self.append_log(msg + "\n")
            self.set_status(msg, tone="err")
            messagebox.showwarning("Close IMVU", msg)
        else:
            msg = "Installer failed. See the log above."
            self.append_log(msg + "\n")
            self.set_status(msg, tone="err")
            messagebox.showerror("Failed", msg)

    def _poll_log_queue(self) -> None:
        while True:
            try:
                item = self.log_queue.get_nowait()
            except queue.Empty:
                break
            if item is None:
                continue
            self.append_log(item)
        self.root.after(100, self._poll_log_queue)


class _QueueStream:
    def __init__(self, target: queue.Queue[str | None]) -> None:
        self.target = target

    def write(self, text: str) -> int:
        if text:
            self.target.put(text)
        return len(text)

    def flush(self) -> None:
        pass


def main() -> int:
    ensure_import_path()
    root = tk.Tk()
    app = InstallerApp(root)
    if "--restore" in sys.argv:
        root.after(200, lambda: app.start_job(restore=True))
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
