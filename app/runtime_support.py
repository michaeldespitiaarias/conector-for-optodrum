"""
Runtime support for the GUI entry point.

Everything here is independent of the application it runs inside, so the
same file is vendored unchanged into every app:

* packaged-build detection and the bundle root (PyInstaller),
* a log file for packaged builds, which have no console to print to,
  plus crash handlers that point the user at that file,
* the window icon,
* consistent sizing across macOS and Windows, and fitting the window to
  smaller screens,
* opening a file or folder with the platform's own handler,
* copying a bundled example project somewhere writable.
"""
from __future__ import annotations

import datetime
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
import traceback

_LOG_MAX_BYTES = 5 * 1024 * 1024
_state = {"app": "App", "log": None, "last_dialog": 0.0}


# ── Packaged build ───────────────────────────────────────────────────────────

def is_frozen() -> bool:
    """True inside a PyInstaller build."""
    return bool(getattr(sys, "frozen", False))


# ── Logging ──────────────────────────────────────────────────────────────────

def log_dir(app_name: str) -> str:
    """Per-user folder for this app's log file."""
    if sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Logs")
    elif sys.platform.startswith("win"):
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return os.path.join(base, app_name, "Logs")
    else:
        base = os.environ.get("XDG_STATE_HOME") or os.path.join(
            os.path.expanduser("~"), ".local", "state")
    return os.path.join(base, app_name)


def log_path() -> str | None:
    """Path of the active log file, or None when logging to a console."""
    return _state["log"]


def _write_log(text: str) -> None:
    path = _state["log"]
    if not path:
        try:
            sys.stderr.write(text)
        except Exception:
            pass
        return
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(text)
    except OSError:
        pass


def start_logging(app_name: str, version: str = "") -> str | None:
    """Send stdout/stderr and uncaught exceptions to a log file.

    Only active when there is no console to print to (a packaged build,
    or `pythonw`). The file is truncated once it grows past 5 MB so it
    never accumulates indefinitely. Returns the log path, or None when
    output stays on the console.
    """
    _state["app"] = app_name
    if not (is_frozen() or sys.stdout is None or sys.stderr is None):
        return None
    folder = log_dir(app_name)
    try:
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"{app_name}.log")
        if os.path.isfile(path) and os.path.getsize(path) > _LOG_MAX_BYTES:
            os.remove(path)
        stream = open(path, "a", encoding="utf-8", buffering=1)
    except OSError:
        return None
    _state["log"] = path
    sys.stdout = stream
    sys.stderr = stream
    stamp = datetime.datetime.now().isoformat(timespec="seconds")
    stream.write(
        f"\n===== {app_name} {version} started {stamp} · "
        f"{platform.platform()} · Python {platform.python_version()} "
        f"({platform.machine()}) =====\n")

    def _excepthook(exc_type, exc, tb):
        _write_log("Uncaught exception:\n"
                   + "".join(traceback.format_exception(exc_type, exc, tb)))

    def _thread_excepthook(args):
        _write_log(f"Uncaught exception in thread {args.thread.name}:\n"
                   + "".join(traceback.format_exception(
                       args.exc_type, args.exc_value, args.exc_traceback)))

    sys.excepthook = _excepthook
    threading.excepthook = _thread_excepthook
    return path


def install_tk_error_handler(root, app_name: str) -> None:
    """Report exceptions raised inside Tk callbacks instead of losing them.

    The traceback always goes to the log (or the console). A dialog tells
    the user something went wrong and where the details are, at most once
    every few seconds so one faulty redraw cannot bury the screen in
    dialogs. Tcl errors about widgets that were already destroyed are a
    harmless side effect of closing a page mid-redraw and are only logged.
    """
    from tkinter import TclError, messagebox

    def handler(exc_type, exc, tb):
        _write_log("Error in a GUI callback:\n"
                   + "".join(traceback.format_exception(exc_type, exc, tb)))
        if issubclass(exc_type, TclError) and (
                "invalid command name" in str(exc)
                or "bad window path" in str(exc)):
            return
        now = time.monotonic()
        if now - _state["last_dialog"] < 5:
            return
        _state["last_dialog"] = now
        where = log_path()
        detail = (f"\n\nThe technical details were saved to:\n{where}"
                  if where else "")
        try:
            messagebox.showerror(
                app_name,
                f"Something went wrong:\n{exc}{detail}\n\nIf it keeps "
                "happening, send that file along with a description of "
                "what you were doing.", parent=root)
        except Exception:
            pass

    root.report_callback_exception = handler


# ── Window ───────────────────────────────────────────────────────────────────

def set_window_icon(root, assets_dir: str) -> None:
    """Show the app's own icon in the title bar, Dock and taskbar."""
    try:
        ico = os.path.join(assets_dir, "app_icon.ico")
        png = os.path.join(assets_dir, "app_icon.png")
        if sys.platform.startswith("win") and os.path.isfile(ico):
            root.iconbitmap(default=ico)
        elif os.path.isfile(png):
            import tkinter as tk
            img = tk.PhotoImage(master=root, file=png)
            if img.width() > 256:
                img = img.subsample(max(1, img.width() // 256))
            root.iconphoto(True, img)
            root._app_icon_image = img   # keep a reference alive
    except Exception:
        pass


def apply_platform_scaling(root) -> None:
    """Render the same layout at the same proportions on every platform.

    Font sizes are given in points. macOS maps one point to one screen
    pixel, Windows to 1.33 pixels, so the same window looks a third
    larger on Windows and its pages overflow. Using macOS's mapping on
    Windows keeps text and fixed-size widgets in their designed ratio;
    Windows' own display-scaling setting still enlarges the whole window
    uniformly. Call right after creating the root, before any widget.
    """
    if sys.platform.startswith("win"):
        try:
            root.tk.call("tk", "scaling", 1.0)
        except Exception:
            pass


def fit_to_screen(root, width: int, height: int,
                  min_width: int, min_height: int) -> None:
    """Size and centre the window so it never exceeds the usable screen.

    A laptop at 1366×768, or a 1080p screen at 150 % scaling, has less
    usable height than the designed window, which would push the bottom
    navigation row (Back / Next) off screen.
    """
    try:
        root.update_idletasks()
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        reserve = 90 if sys.platform.startswith("win") else 110
        w = max(640, min(width, sw - 40))
        h = max(480, min(height, sh - reserve))
        root.minsize(min(min_width, w), min(min_height, h))
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - reserve - h) // 2)
        root.geometry(f"{w}x{h}+{x}+{y}")
    except Exception:
        pass


# ── Files ────────────────────────────────────────────────────────────────────

def open_path(path: str) -> bool:
    """Open a file or folder with the platform's default application.

    Returns False when *path* does not exist or could not be opened.
    """
    if not path or not os.path.exists(path):
        return False
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", path])
        elif sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", path])
        return True
    except Exception as exc:
        _write_log(f"Could not open {path}: {exc}\n")
        return False


def examples_home(app_name: str) -> str:
    """Writable folder the bundled examples are copied into."""
    home = os.path.expanduser("~")
    docs = os.path.join(home, "Documents")
    return os.path.join(docs if os.path.isdir(docs) else home,
                        f"{app_name} examples")


def bundled_examples(samples_data_dir: str) -> list:
    """Names of the example projects shipped under *samples_data_dir*."""
    if not os.path.isdir(samples_data_dir):
        return []
    return sorted(n for n in os.listdir(samples_data_dir)
                  if not n.startswith(".")
                  and os.path.isdir(os.path.join(samples_data_dir, n)))


def install_example(app_name: str, samples_data_dir: str, name: str) -> dict:
    """Copy one bundled example project somewhere writable.

    The app bundle itself is read-only (and on macOS may be relocated to a
    temporary path), so an example is copied to
    ``~/Documents/<App> examples/data/<name>`` the first time it is used;
    a copy that already exists is reused, so edits made to it survive.
    The example's bundled results (``samples/output/<name>``, beside the
    data folder), when present, are copied too, so that an example that
    ships only the tables its statistical analysis reads opens with them.
    Returns ``{"data": ..., "output": ..., "project": name}``.
    """
    root = examples_home(app_name)
    data = os.path.join(root, "data", name)
    output = os.path.join(root, "output")
    if not os.path.isdir(data):
        src = os.path.join(samples_data_dir, name)
        if not os.path.isdir(src):
            raise FileNotFoundError(f"Example {name!r} is not bundled.")
        shutil.copytree(src, data,
                        ignore=shutil.ignore_patterns(".DS_Store"))
    os.makedirs(output, exist_ok=True)
    baked = os.path.join(os.path.dirname(os.path.abspath(samples_data_dir)),
                         "output", name)
    target = os.path.join(output, name)
    if os.path.isdir(baked) and not os.path.isdir(target):
        shutil.copytree(baked, target,
                        ignore=shutil.ignore_patterns(".DS_Store"))
    return {"data": data, "output": output, "project": name}


# ── Per-user settings ────────────────────────────────────────────────────────

def config_dir(app_name: str) -> str:
    """Per-user folder for settings. VISOLAB_SETTINGS_DIR overrides it
    (the test suites point it at a temporary folder)."""
    override = os.environ.get("VISOLAB_SETTINGS_DIR")
    if override:
        return os.path.join(override, app_name)
    if sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library",
                            "Application Support")
    elif sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
            os.path.expanduser("~"), ".config")
    return os.path.join(base, app_name)


def load_settings(app_name: str) -> dict:
    """The saved settings, or an empty dict when there are none (or the
    file cannot be read, which must never stop the app from starting)."""
    import json
    path = os.path.join(config_dir(app_name), "settings.json")
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_settings(app_name: str, settings: dict) -> None:
    import json
    folder = config_dir(app_name)
    try:
        os.makedirs(folder, exist_ok=True)
        tmp = os.path.join(folder, "settings.json.tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(settings, fh, indent=2, ensure_ascii=False)
        os.replace(tmp, os.path.join(folder, "settings.json"))
    except OSError as exc:
        _write_log(f"Could not save settings: {exc}\n")


def remember_recent(app_name: str, path: str, label: str,
                    limit: int = 8) -> list:
    """Put *path* at the top of the recent-analyses list and return it."""
    settings = load_settings(app_name)
    recent = [r for r in settings.get("recent", [])
              if isinstance(r, dict) and r.get("path") != path]
    recent.insert(0, {"path": path, "label": label,
                      "when": datetime.datetime.now().isoformat(
                          timespec="minutes")})
    settings["recent"] = recent[:limit]
    save_settings(app_name, settings)
    return settings["recent"]


def recent_analyses(app_name: str) -> list:
    """Recent analyses whose file still exists, newest first."""
    return [r for r in load_settings(app_name).get("recent", [])
            if isinstance(r, dict) and os.path.isfile(r.get("path", ""))]


# ── Provenance ────────────────────────────────────────────────────────────────
_PROVENANCE_PACKAGES = ("numpy", "pandas", "scipy", "statsmodels",
                        "scikit-learn", "matplotlib", "plotly")


def _sha256(path: str) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def provenance(app_name: str, version: str, data_folder: str = "",
               files=()) -> dict:
    """What produced a run: the application and its version, Python, the
    operating system, the versions of the analysis packages, a SHA-256 of
    each of *files* (the tables analysed) and, for *data_folder*, the
    number of files, their total size and a SHA-256 of their names and
    sizes, which changes whenever a file is added, removed or rewritten
    with another size."""
    import datetime
    import hashlib
    import platform
    from importlib import metadata as importlib_metadata
    packages = {}
    for name in _PROVENANCE_PACKAGES:
        try:
            packages[name] = importlib_metadata.version(name)
        except Exception:                               # noqa: BLE001
            continue
    out = {"app": app_name, "version": version,
           "python": platform.python_version(),
           "platform": f"{platform.system()} {platform.release()} "
                       f"({platform.machine()})",
           "packages": packages,
           "time": datetime.datetime.now().isoformat(timespec="seconds"),
           "files": {}}
    for path in files or ():
        if path and os.path.isfile(path):
            try:
                out["files"][os.path.basename(path)] = _sha256(path)
            except OSError:
                continue
    if data_folder and os.path.isdir(data_folder):
        listing, total = [], 0
        for root, _dirs, names in os.walk(data_folder):
            for name in names:
                full = os.path.join(root, name)
                try:
                    size = os.path.getsize(full)
                except OSError:
                    continue
                total += size
                listing.append(f"{os.path.relpath(full, data_folder)}\t{size}")
        listing.sort()
        out["data_folder"] = {
            "files": len(listing), "bytes": total,
            "listing_sha256": hashlib.sha256(
                "\n".join(listing).encode("utf-8")).hexdigest()}
    return out
