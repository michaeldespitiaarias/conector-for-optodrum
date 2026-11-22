"""
Interface language: every piece of interface text has a Spanish entry,
translations keep their placeholders, and nothing translatable is left
showing in English once Spanish is active.

The static checks read the source, so a new tr("...") call without an
entry fails here rather than surfacing as a half-English page.
"""
import ast
import os
import re
import string
import sys

import pytest

_APP = os.path.join(os.path.dirname(__file__), "..", "app")
sys.path.insert(0, _APP)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..",
                                "helpers"))

import i18n  # noqa: E402
import locale_es  # noqa: E402

# Helpers that pass one of their own arguments through tr(): name ->
# (positional indexes, keyword names).
_HELPERS = {
    "_section": ([1], []), "_labeled_entry": ([1], ["hint"]),
}
# Module tables whose text the GUI shows through tr().
_TABLES = ("_WIZARD_LABELS", "_HELP_CONTENT", "_HOME_INTRO", "TAGLINE")
# Table entries that are identifiers, not text.
_CODE_TOKEN = re.compile(r"^[a-z0-9_]+$")


def _heading(text):
    return text[0] + text[1:].lower() if text.isupper() else text


def _interface_strings():
    out = set()
    for fname in os.listdir(_APP):
        if not fname.endswith(".py") or fname.startswith("locale_"):
            continue
        with open(os.path.join(_APP, fname), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                name = fn.id if isinstance(fn, ast.Name) else (
                    fn.attr if isinstance(fn, ast.Attribute) else None)
                if name in ("tr", "trf", "plural"):
                    for arg in node.args[: 2 if name == "plural" else 1]:
                        if isinstance(arg, ast.Constant):
                            out.add(arg.value)
                spec = _HELPERS.get(name)
                if spec:
                    for pos in spec[0]:
                        if len(node.args) > pos and isinstance(
                                node.args[pos], ast.Constant):
                            out.add(_heading(node.args[pos].value))
                    for kw in node.keywords:
                        if kw.arg in spec[1] and isinstance(kw.value,
                                                            ast.Constant):
                            out.add(kw.value.value)
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id in _TABLES:
                        for n in ast.walk(node.value):
                            if isinstance(n, ast.Constant) and isinstance(
                                    n.value, str):
                                out.add(n.value)
    return {s for s in out
            if isinstance(s, str) and s.strip()
            and not _CODE_TOKEN.match(s)}


def _covered(text):
    if text in locale_es.STRINGS:
        return True
    return any(re.fullmatch(rx, text) for rx, _ in locale_es.PATTERNS)


def test_every_interface_string_has_a_spanish_entry():
    missing = sorted(s for s in _interface_strings() if not _covered(s))
    assert not missing, "untranslated:\n" + "\n".join(
        repr(s[:90]) for s in missing)


def _run_messages():
    """Progress lines, message boxes and the reasons a step cannot
    continue: text the page walk below never shows, because nothing is
    run and no step is refused."""
    out = set()
    for fname in os.listdir(_APP):
        if not fname.endswith(".py") or fname.startswith("locale_"):
            continue
        with open(os.path.join(_APP, fname), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                name = fn.attr if isinstance(fn, ast.Attribute) else getattr(
                    fn, "id", None)
                picks = {"_post": node.args[1:2],
                         "showwarning": node.args[1:2],
                         "showerror": node.args[1:2],
                         "showinfo": node.args[1:2]}.get(name, [])
                for arg in picks:
                    if isinstance(arg, ast.Constant) and isinstance(
                            arg.value, str):
                        out.add(arg.value)
            if (isinstance(node, ast.Return)
                    and isinstance(node.value, ast.Tuple)
                    and len(node.value.elts) == 2
                    and isinstance(node.value.elts[0], ast.Constant)
                    and node.value.elts[0].value is False
                    and isinstance(node.value.elts[1], ast.Constant)
                    and isinstance(node.value.elts[1].value, str)):
                out.add(node.value.elts[1].value)
    return {s for s in out if s.strip()}


def test_run_and_validation_messages_have_a_spanish_entry():
    missing = sorted(s for s in _run_messages() if not _covered(s))
    assert not missing, "untranslated:\n" + "\n".join(
        repr(s[:90]) for s in missing)


def _fields(template):
    return sorted(f for _, f, _, _ in string.Formatter().parse(template)
                  if f is not None)


@pytest.mark.parametrize("key", sorted(k for k in locale_es.STRINGS
                                       if "{" in k))
def test_translations_keep_their_placeholders(key):
    assert _fields(key) == _fields(locale_es.STRINGS[key])


def test_patterns_compile_and_use_only_their_own_groups():
    for rx, template in locale_es.PATTERNS:
        n = re.compile(rx).groups
        used = [f for f in _fields(template) if f.isdigit()]
        assert all(int(f) < n for f in used), rx


def test_english_is_the_identity():
    i18n.set_language("en")
    assert i18n.tr("Next") == "Next"
    assert i18n.trf("{n} levels", n=3) == "3 levels"


def test_spanish_translates_and_falls_back():
    try:
        assert i18n.set_language("es") == "es"
        assert i18n.tr("Back") == "Atrás"
        # Text with no entry comes back unchanged, never blank.
        assert i18n.tr("contrast_0.011_cycles") == "contrast_0.011_cycles"
        assert i18n.set_language("xx") == "en"
    finally:
        i18n.set_language("en")


# ── Runtime: walk every page in Spanish ──────────────────────────────────
tk = pytest.importorskip("tkinter")


def _display_available():
    try:
        r = tk.Tk()
        r.destroy()
        return True
    except Exception:
        return False


def _visible_texts(widget):
    from widgets import CheckBox, RoundedButton, SegmentedControl
    out = []
    stack = [widget]
    while stack:
        w = stack.pop()
        stack.extend(w.winfo_children())
        if isinstance(w, tk.Label):
            out.append(w.cget("text"))
        elif isinstance(w, RoundedButton):
            out.append(w._text)
        elif isinstance(w, CheckBox) and w._label is not None:
            out.append(w._label.cget("text"))
        elif isinstance(w, SegmentedControl):
            out.extend(label for _v, label in w._opts)
    return [t for t in out if isinstance(t, str) and t.strip()]


@pytest.mark.skipif(not _display_available(),
                    reason="no display available for tkinter")
def test_no_page_shows_english_once_spanish_is_active(tmp_path,
                                                      monkeypatch):
    import importlib.util

    import tkinter.messagebox as mb
    for name in ("showwarning", "showerror", "showinfo"):
        monkeypatch.setattr(mb, name, lambda *a, **k: None)
    monkeypatch.setenv("VISOLAB_SETTINGS_DIR", str(tmp_path / "settings"))

    sys.path.insert(0, os.path.join(_APP, "..", "steps", "optodrum"))
    spec = importlib.util.spec_from_file_location(
        "optodrum_gui_i18n", os.path.join(_APP, "OptoDrum Connector GUI.py"))
    gui = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gui)
    app = gui.OptoDrumApp()
    same = {k for k, v in locale_es.STRINGS.items() if k == v}
    leaks = {}
    untranslated = set()
    produced = set(locale_es.STRINGS.values())
    real_tr, real_trf, real_plural = i18n.tr, i18n.trf, i18n.plural

    def spy(text):
        out = real_tr(text)
        if (out == text and isinstance(text, str) and text not in same
                and text not in produced
                and re.search(r"[A-Za-z]{3}", text)):
            untranslated.add(text)
        produced.add(out)
        return out

    def spy_f(template, **values):
        out = real_trf(template, **values)
        produced.add(out)
        return out
    for module in (gui, i18n):
        monkeypatch.setattr(module, "tr", spy)
        monkeypatch.setattr(module, "trf", spy_f)
    try:
        app._set_language("es")

        def check(where):
            app.root.update_idletasks()
            for t in _visible_texts(app.root):
                if t in locale_es.STRINGS and t not in same:
                    leaks.setdefault(t, where)

        check("welcome")
        app._show_home()
        check("home")
        sample = os.path.join(_APP, "..", "samples", "data", "Demo Project")
        app.data_var.set(sample)
        app.output_var.set(str(tmp_path))
        app.project_var.set("Demo")
        check("home, folders set")
        app._show_running()
        check("running")
        app._do_run()
        app._run_finished()
        check("finished")
        app._show_running()
        app._run_failed("x")
        check("failed")
        app._show_running()
        app._run_cancelled()
        check("cancelled")
    finally:
        try:
            app.root.destroy()
        finally:
            i18n.set_language("en")
    assert not leaks, "shown in English:\n" + "\n".join(
        f"{where}: {t[:80]!r}" for t, where in leaks.items())
    assert not untranslated, "no Spanish entry:\n" + "\n".join(
        repr(t[:90]) for t in sorted(untranslated))
