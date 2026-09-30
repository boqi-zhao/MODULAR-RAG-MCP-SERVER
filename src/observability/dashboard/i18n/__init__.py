"""Dashboard internationalisation (i18n) package.

Public API::

    from src.observability.dashboard.i18n import t, render_language_selector

    st.header(t("overview.header"))          # → "📊 系统总览"
    st.metric(t("overview.total_traces"), 42)

Supported languages
-------------------
``zh`` (default) and ``en``.  The active language lives in
``st.session_state["lang"]`` and can be changed at runtime via the
selector rendered by :func:`render_language_selector`.
"""

from __future__ import annotations

from .catalog import CATALOG, DEFAULT_LANG, LANG_LABELS, SUPPORTED_LANGS
from .translator import (
    get_lang,
    render_language_selector,
    set_lang,
    stage_label,
    t,
    translate_mapping,
)

__all__ = [
    "CATALOG",
    "DEFAULT_LANG",
    "LANG_LABELS",
    "SUPPORTED_LANGS",
    "get_lang",
    "render_language_selector",
    "set_lang",
    "stage_label",
    "t",
    "translate_mapping",
]
