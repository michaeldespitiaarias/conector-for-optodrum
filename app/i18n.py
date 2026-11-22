"""
Interface language (identical in every VisoLab application).

The English text in the source is the key: ``tr("Next")`` returns the
Spanish entry of ``locale_es.STRINGS`` when Spanish is active, and the
English text itself otherwise, so a string nobody has translated yet
still reads correctly instead of breaking. ``trf`` formats a translated
template: ``trf("Loaded {n} rows", n=12)``.

Only interface text goes through here. Data values (column names, group
levels, file names) never do: a column called "Group" must stay "Group".
Generated reports and figures stay in English, the language they are
published in.
"""
from __future__ import annotations

import re

LANGUAGES = (("en", "English"), ("es", "Español"))

_state = {"lang": "en", "table": {}, "patterns": []}


def set_language(code: str) -> str:
    """Activate *code* ("en" or "es"); unknown codes fall back to English.
    Returns the code actually in force."""
    table, patterns = {}, []
    if code == "es":
        try:
            import locale_es
            table = locale_es.STRINGS
            patterns = [(re.compile(rx), tpl) for rx, tpl
                        in getattr(locale_es, "PATTERNS", [])]
        except ImportError:
            code = "en"
    else:
        code = "en"
    _state["lang"] = code
    _state["table"] = table
    _state["patterns"] = patterns
    return code


def language() -> str:
    return _state["lang"]


def tr(text: str) -> str:
    """Translate *text*; messages built at run time (a column name or a
    count inside them) are matched against the locale's PATTERNS, whose
    captured groups are passed through untranslated."""
    if not text or _state["lang"] == "en":
        return text
    hit = _state["table"].get(text)
    if hit is not None:
        return hit
    for rx, template in _state["patterns"]:
        m = rx.fullmatch(text)
        if m:
            return template.format(*m.groups(), **m.groupdict())
    return text


def trf(template: str, **values) -> str:
    return tr(template).format(**values)


def plural(n: int, one: str, many: str) -> str:
    """Translated singular or plural template, formatted with ``n``."""
    return trf(one if n == 1 else many, n=n)
