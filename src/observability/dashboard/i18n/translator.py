"""Translation runtime: language state, ``t()`` lookup, and the UI selector.

The active language is stored in ``st.session_state["lang"]`` so it survives
Streamlit's rerun-per-interaction model.  :func:`get_lang` is defensive: it
works even when called outside a Streamlit script run (e.g. from a unit test)
by falling back to :data:`~.catalog.DEFAULT_LANG`.
"""

from __future__ import annotations

from typing import Any, Mapping

import streamlit as st

from .catalog import CATALOG, DEFAULT_LANG, LANG_LABELS, SUPPORTED_LANGS

# session_state key holding the active language code
_LANG_KEY = "lang"


def get_lang() -> str:
    """Return the active language code, defaulting to ``zh``.

    Falls back to :data:`DEFAULT_LANG` when Streamlit's session state is
    unavailable or holds an unsupported value.
    """
    try:
        lang = st.session_state.get(_LANG_KEY, DEFAULT_LANG)
    except Exception:
        return DEFAULT_LANG
    return lang if lang in SUPPORTED_LANGS else DEFAULT_LANG


def set_lang(lang: str) -> None:
    """Set the active language code.

    Unknown codes are ignored so a stale persisted value cannot put the UI
    into a language with no catalog entries.
    """
    if lang not in SUPPORTED_LANGS:
        return
    try:
        st.session_state[_LANG_KEY] = lang
    except Exception:
        pass


def t(key: str, **kwargs: Any) -> str:
    """Translate ``key`` into the active language.

    Missing keys and missing translations fall back to the default language,
    then to the key itself — so an incomplete catalog degrades to a readable
    label rather than raising.

    Parameters
    ----------
    key:
        Catalog key, e.g. ``"overview.header"`` or
        ``"ingestion.stage.load"``.  For pipeline stage names the
        ``ingestion.stage.`` prefix is optional.
    **kwargs:
        Values interpolated into the translation via :meth:`str.format`.
        Formatting errors never propagate: the raw template is returned.
    """
    entry = CATALOG.get(key)

    # Allow bare stage names ("load") as a convenience for pipeline callbacks.
    if entry is None and not key.startswith("ingestion.stage."):
        entry = CATALOG.get(f"ingestion.stage.{key}")

    if entry is None:
        return key

    lang = get_lang()
    text = entry.get(lang) or entry.get(DEFAULT_LANG) or key

    if not kwargs:
        return text
    try:
        return text.format(**kwargs)
    except (KeyError, IndexError, ValueError):
        # Never let a placeholder mismatch break a page render.
        return text


def render_language_selector(*, container: Any = None) -> str:
    """Render the language switcher and return the active language code.

    Uses ``st.segmented_control`` when available (Streamlit ≥ 1.40) and
    falls back to a radio group otherwise.  Selecting a language triggers a
    rerun, so the caller does not need to do anything with the return value
    beyond reading it.
    """
    target = container if container is not None else st.sidebar
    current = get_lang()
    codes = list(SUPPORTED_LANGS)
    labels = [LANG_LABELS[c] for c in codes]

    with target:
        st.caption(t("app.sidebar_language"))

        if hasattr(st, "segmented_control"):
            choice = st.segmented_control(
                "Language",
                options=labels,
                default=LANG_LABELS[current],
                key="lang_selector",
                label_visibility="collapsed",
            )
        else:  # pragma: no cover - depends on Streamlit version
            choice = st.radio(
                "Language",
                options=labels,
                index=codes.index(current),
                key="lang_selector",
                label_visibility="collapsed",
                horizontal=True,
            )

    # `segmented_control` can return None when the user clears the selection.
    if choice in labels:
        selected = codes[labels.index(choice)]
        if selected != current:
            set_lang(selected)
            st.rerun()

    return current


def stage_label(stage: str) -> str:
    """Translate a raw pipeline stage name, echoing it back when unknown.

    Unlike :func:`t`, an unknown stage yields the bare stage name rather
    than the catalog key, so progress callbacks for new pipeline stages
    still show something readable.
    """
    key = f"ingestion.stage.{stage}"
    return t(key) if key in CATALOG else stage


def translate_mapping(mapping: Mapping[str, str]) -> dict[str, str]:
    """Translate a mapping of ``{label_key: value}`` into the active language.

    Handy for pandas/Streamlit tables whose column headers are catalog keys.
    """
    return {t(key): value for key, value in mapping.items()}
