"""Modular RAG Dashboard – multi-page Streamlit application.

Entry-point: ``streamlit run src/observability/dashboard/app.py``

Pages are registered via ``st.navigation()`` and rendered by their
respective modules under ``pages/``.  Page titles and the language
switcher are driven by :mod:`src.observability.dashboard.i18n`.
"""

from __future__ import annotations

import streamlit as st

from src.observability.dashboard.i18n import render_language_selector, t


# ── Page definitions ─────────────────────────────────────────────────

def _page_overview() -> None:
    from src.observability.dashboard.pages.overview import render
    render()


def _page_data_browser() -> None:
    from src.observability.dashboard.pages.data_browser import render
    render()


def _page_ingestion_manager() -> None:
    from src.observability.dashboard.pages.ingestion_manager import render
    render()


def _page_ingestion_traces() -> None:
    from src.observability.dashboard.pages.ingestion_traces import render
    render()


def _page_query_traces() -> None:
    from src.observability.dashboard.pages.query_traces import render
    render()


def _page_evaluation_panel() -> None:
    from src.observability.dashboard.pages.evaluation_panel import render
    render()


# ── Navigation ───────────────────────────────────────────────────────

def _build_pages() -> list:
    """Build the navigation registry, localised to the active language.

    Called on every rerun so switching language relabels the sidebar
    navigation without restarting the server.
    """
    return [
        st.Page(_page_overview, title=t("nav.overview"), icon="📊", default=True),
        st.Page(_page_data_browser, title=t("nav.data_browser"), icon="🔍"),
        st.Page(_page_ingestion_manager, title=t("nav.ingestion_manager"), icon="📥"),
        st.Page(_page_ingestion_traces, title=t("nav.ingestion_traces"), icon="🔬"),
        st.Page(_page_query_traces, title=t("nav.query_traces"), icon="🔎"),
        st.Page(_page_evaluation_panel, title=t("nav.evaluation_panel"), icon="📏"),
    ]


def main() -> None:
    st.set_page_config(
        page_title=t("app.page_title"),
        page_icon="📊",
        layout="wide",
    )

    # Language switcher lives in the sidebar so it is reachable from
    # every page.  Changing it reruns the script, which re-localises
    # both the nav labels and the page body.
    render_language_selector()

    nav = st.navigation(_build_pages())
    nav.run()


if __name__ == "__main__":
    main()
else:
    # When run directly via `streamlit run app.py`
    main()
