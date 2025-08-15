from __future__ import annotations
import gettext
import os
from typing import Any

_trans: gettext.NullTranslations | gettext.GNUTranslations | None = None

def set_language(lang: str = "en") -> None:
    global _trans
    localedir = os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        "locales",
    )
    _trans = gettext.translation(
        domain="messages",
        localedir=localedir,
        languages=[lang],
        fallback=True,
    )

def _(msg: str) -> str:
    if _trans is None:
        set_language("en")
    return _trans.gettext(msg) if _trans else msg
