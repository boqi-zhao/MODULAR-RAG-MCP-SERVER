"""Data Browser page – browse ingested documents, chunks, and images.

Layout:
1. Collection selector (sidebar)
2. Document list with chunk counts
3. Expandable document detail → chunk cards with text + metadata
4. Image preview gallery
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.observability.dashboard.i18n import t
from src.observability.dashboard.services.data_service import DataService


def render() -> None:
    """Render the Data Browser page."""
    st.header(t("browser.header"))

    try:
        svc = DataService()
    except Exception as exc:
        st.error(t("browser.service_init_failed", error=exc))
        return

    # ── Collection selector ────────────────────────────────────────
    collections = svc.list_collections()
    if "default" not in collections:
        collections.insert(0, "default")
    collection = st.selectbox(
        t("browser.collection"),
        options=collections,
        index=0,
        key="db_collection_filter",
    )
    coll_arg = collection if collection else None

    # ── Danger zone: clear all data ────────────────────────────────
    st.divider()
    with st.expander(t("browser.danger_zone"), expanded=False):
        st.warning(t("browser.danger_warning"))
        col_btn, col_status = st.columns([1, 2])
        with col_btn:
            if st.button(t("browser.clear_all"), type="primary", key="btn_clear_all"):
                st.session_state["confirm_clear"] = True

        if st.session_state.get("confirm_clear"):
            st.error(t("browser.confirm_prompt"))
            c1, c2, _ = st.columns([1, 1, 2])
            with c1:
                if st.button(t("browser.confirm_yes"), key="btn_confirm_clear"):
                    result = svc.reset_all()
                    st.session_state["confirm_clear"] = False
                    if result["errors"]:
                        st.warning(
                            t(
                                "browser.cleared_with_errors",
                                count=len(result["errors"]),
                                errors="; ".join(result["errors"]),
                            )
                        )
                    else:
                        st.success(
                            t(
                                "browser.cleared_success",
                                count=result["collections_deleted"],
                            )
                        )
                    st.rerun()
            with c2:
                if st.button(t("browser.cancel"), key="btn_cancel_clear"):
                    st.session_state["confirm_clear"] = False
                    st.rerun()

    st.divider()

    # ── Document list ──────────────────────────────────────────────
    try:
        docs = svc.list_documents(coll_arg)
    except Exception as exc:
        st.error(t("browser.docs_load_failed", error=exc))
        return

    if not docs:
        st.info(t("browser.no_documents"))
        return

    st.subheader(t("browser.documents_count", count=len(docs)))

    for idx, doc in enumerate(docs):
        source_name = Path(doc["source_path"]).name
        label = t(
            "browser.doc_expander",
            name=source_name,
            chunks=doc["chunk_count"],
            images=doc["image_count"],
        )
        with st.expander(label, expanded=(len(docs) == 1)):
            # ── Document metadata ──────────────────────────────────
            col_a, col_b, col_c = st.columns(3)
            col_a.metric(t("common.chunks"), doc["chunk_count"])
            col_b.metric(t("common.images"), doc["image_count"])
            col_c.metric(t("browser.collection"), doc.get("collection", "—"))
            st.caption(
                f"**{t('common.source')}:** {doc['source_path']}  ·  "
                f"**{t('browser.hash_label')}:** `{doc['source_hash'][:16]}…`  ·  "
                f"**{t('browser.processed_at')}:** {doc.get('processed_at', '—')}"
            )

            st.divider()

            # ── Chunk cards ────────────────────────────────────────
            chunks = svc.get_chunks(doc["source_hash"], coll_arg)
            if chunks:
                st.markdown(t("browser.chunks_count", count=len(chunks)))
                for cidx, chunk in enumerate(chunks):
                    text = chunk.get("text", "")
                    meta = chunk.get("metadata", {})
                    chunk_id = chunk["id"]

                    # Title from metadata or first line
                    title = meta.get("title", "")
                    if not title:
                        title = text[:60].replace("\n", " ").strip()
                        if len(text) > 60:
                            title += "…"

                    with st.container(border=True):
                        st.markdown(
                            t(
                                "browser.chunk_meta",
                                index=cidx + 1,
                                chunk_id=chunk_id[-16:],
                                chars=len(text),
                            )
                        )
                        # Show the actual chunk text (scrollable)
                        _height = max(120, min(len(text) // 2, 600))
                        st.text_area(
                            t("common.content"),
                            value=text,
                            height=_height,
                            disabled=True,
                            key=f"chunk_text_{idx}_{cidx}",
                            label_visibility="collapsed",
                        )
                        # Expandable metadata
                        with st.expander(t("common.metadata"), expanded=False):
                            st.json(meta)
            else:
                st.caption(t("browser.no_chunks"))

            # ── Image preview ──────────────────────────────────────
            images = svc.get_images(doc["source_hash"], coll_arg)
            if images:
                st.divider()
                st.markdown(t("browser.images_count", count=len(images)))
                img_cols = st.columns(min(len(images), 4))
                for iidx, img in enumerate(images):
                    with img_cols[iidx % len(img_cols)]:
                        img_path = Path(img.get("file_path", ""))
                        if img_path.exists():
                            st.image(str(img_path), caption=img["image_id"], width=200)
                        else:
                            st.caption(t("common.file_missing", name=img["image_id"]))
