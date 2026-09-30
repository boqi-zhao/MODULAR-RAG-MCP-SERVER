"""Ingestion Traces page – browse ingestion trace history with per-stage detail.

Layout:
1. Trace list (reverse-chronological, filtered to trace_type=="ingestion")
2. Pipeline overview: source file, total time, stage timing waterfall
3. Per-stage detail tabs:
   📄 Load    – raw document text preview
   ✂️ Split   – chunk list with text
   🔄 Transform – before/after diff, enrichment metadata
   🔢 Embed   – vector stats
   💾 Upsert  – stored IDs
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import streamlit as st

from src.observability.dashboard.i18n import t
from src.observability.dashboard.services.trace_service import TraceService

logger = logging.getLogger(__name__)


def render() -> None:
    """Render the Ingestion Traces page."""
    st.header(t("ingestion_traces.header"))

    svc = TraceService()
    traces = svc.list_traces(trace_type="ingestion")

    if not traces:
        st.info(t("ingestion_traces.none"))
        return

    st.subheader(t("ingestion_traces.history", count=len(traces)))

    for idx, trace in enumerate(traces):
        trace_id = trace.get("trace_id", "unknown")
        started = trace.get("started_at", "—")
        total_ms = trace.get("elapsed_ms")
        total_label = f"{total_ms:.0f} ms" if total_ms is not None else "—"
        meta = trace.get("metadata", {})
        source_path = meta.get("source_path", "—")

        # Build expander title
        file_name = source_path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1] if source_path != "—" else "—"
        expander_title = f"📄 **{file_name}** · {total_label} · {started[:19]}"

        with st.expander(expander_title, expanded=(idx == 0)):
            timings = svc.get_stage_timings(trace)
            stages_by_name = {t["stage_name"]: t for t in timings}

            # ── 1. Overview metrics ────────────────────────────
            st.markdown(t("ingestion_traces.pipeline_overview"))
            st.caption(t("ingestion_traces.source_line", path=source_path))

            load_d = stages_by_name.get("load", {}).get("data", {})
            split_d = stages_by_name.get("split", {}).get("data", {})
            transform_d = stages_by_name.get("transform", {}).get("data", {})
            embed_d = stages_by_name.get("embed", {}).get("data", {})
            upsert_d = stages_by_name.get("upsert", {}).get("data", {})

            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                st.metric(
                    t("ingestion_traces.doc_length"),
                    t("common.chars", count=f"{load_d.get('text_length', 0):,}"),
                )
            with c2:
                st.metric(t("ingestion_traces.chunks"), split_d.get("chunk_count", 0))
            with c3:
                st.metric(t("ingestion_traces.images"), load_d.get("image_count", 0))
            with c4:
                st.metric(t("ingestion_traces.vectors"), upsert_d.get("vector_count", 0))
            with c5:
                st.metric(t("ingestion_traces.total_time"), total_label)

            st.divider()

            # ── 2. Stage timing waterfall ──────────────────────
            # Filter to main pipeline stages only (not sub-stages)
            main_stages = [
                stage for stage in timings
                if stage["stage_name"] in ("load", "split", "transform", "embed", "upsert")
            ]
            if main_stages:
                st.markdown(t("ingestion_traces.stage_timings"))
                chart_data = {
                    stage["stage_name"]: stage["elapsed_ms"] for stage in main_stages
                }
                st.bar_chart(chart_data, horizontal=True)
                st.table([
                    {
                        t("col.stage"): stage["stage_name"],
                        t("col.elapsed_ms"): round(stage["elapsed_ms"], 2),
                    }
                    for stage in main_stages
                ])

            # ── Diagnostics ───────────────────────────────────
            _render_ingestion_diagnostics(stages_by_name, load_d, split_d, transform_d, embed_d, upsert_d)

            st.divider()

            # ── 3. Per-stage detail tabs ───────────────────────
            st.markdown(t("ingestion_traces.stage_details"))

            tab_defs = []
            _TAB_KEYS = {
                "load": "ingestion_traces.load_tab",
                "split": "ingestion_traces.split_tab",
                "transform": "ingestion_traces.transform_tab",
                "embed": "ingestion_traces.embed_tab",
                "upsert": "ingestion_traces.upsert_tab",
            }
            for _stage_key, _label_key in _TAB_KEYS.items():
                if _stage_key in stages_by_name:
                    tab_defs.append((t(_label_key), _stage_key))

            if tab_defs:
                tabs = st.tabs([label for label, _ in tab_defs])
                for tab, (label, key) in zip(tabs, tab_defs):
                    with tab:
                        stage = stages_by_name[key]
                        data = stage.get("data", {})
                        elapsed = stage.get("elapsed_ms")
                        if elapsed is not None:
                            st.caption(f"⏱️ {elapsed:.1f} ms")

                        if key == "load":
                            _render_load_stage(data, trace_idx=idx)
                        elif key == "split":
                            _render_split_stage(data, trace_idx=idx)
                        elif key == "transform":
                            _render_transform_stage(data, trace_idx=idx)
                        elif key == "embed":
                            _render_embed_stage(data)
                        elif key == "upsert":
                            _render_upsert_stage(data)
            else:
                st.info(t("ingestion_traces.no_stage_details"))


def _render_ingestion_diagnostics(
    stages_by_name: Dict[str, Any],
    load_d: Dict[str, Any],
    split_d: Dict[str, Any],
    transform_d: Dict[str, Any],
    embed_d: Dict[str, Any],
    upsert_d: Dict[str, Any],
) -> None:
    """Render diagnostic hints for ingestion pipeline stages."""
    expected = ["load", "split", "transform", "embed", "upsert"]
    present = [s for s in expected if s in stages_by_name]
    missing = [s for s in expected if s not in stages_by_name]

    if missing:
        missing_labels = {
            "load": t("ingestion_traces.load_tab"),
            "split": t("ingestion_traces.split_tab"),
            "transform": t("ingestion_traces.transform_tab"),
            "embed": t("ingestion_traces.embed_tab"),
            "upsert": t("ingestion_traces.upsert_tab"),
        }
        names = ", ".join(missing_labels.get(m, m) for m in missing)
        if "load" in missing:
            st.error(t("ingestion_traces.pipeline_incomplete_load", names=names))
        else:
            st.warning(t("ingestion_traces.pipeline_incomplete", names=names))

    # Stage-specific diagnostics
    if "load" in stages_by_name and load_d.get("text_length", 0) == 0:
        st.warning(t("ingestion_traces.empty_text"))

    if "split" in stages_by_name and split_d.get("chunk_count", 0) == 0:
        st.warning(t("ingestion_traces.zero_chunks"))

    if "transform" in stages_by_name:
        refined_llm = transform_d.get("refined_by_llm", 0)
        refined_rule = transform_d.get("refined_by_rule", 0)
        if refined_llm == 0 and refined_rule == 0:
            st.info(t("ingestion_traces.no_refine"))

    if "embed" in stages_by_name and embed_d.get("dense_vector_count", 0) == 0:
        st.warning(t("ingestion_traces.zero_vectors"))

    if "upsert" in stages_by_name:
        vec_count = upsert_d.get("vector_count", upsert_d.get("dense_store", {}).get("count", 0))
        if vec_count == 0:
            st.warning(t("ingestion_traces.zero_upsert"))

    # Check for error fields in any stage data
    for stage_name in present:
        stage_data = stages_by_name[stage_name].get("data", {})
        err = stage_data.get("error", "")
        if err:
            label = stage_name.replace("_", " ").title()
            st.error(t("ingestion_traces.stage_error", stage=label, error=err))


# ═══════════════════════════════════════════════════════════════
# Per-stage renderers
# ═══════════════════════════════════════════════════════════════

def _render_load_stage(data: Dict[str, Any], *, trace_idx: int = 0) -> None:
    """Render Load stage: raw document preview."""
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(t("ingestion_traces.doc_id"), data.get("doc_id", "—")[:16])
    with c2:
        st.metric(
            t("ingestion_traces.text_length"), f"{data.get('text_length', 0):,}"
        )
    with c3:
        st.metric(t("ingestion_traces.images"), data.get("image_count", 0))

    preview = data.get("text_preview", "")
    if preview:
        st.markdown(t("ingestion_traces.raw_text"))
        st.text_area(
            t("field.raw_document_text"),
            value=preview,
            height=max(120, min(len(preview) // 2, 600)),
            disabled=True,
            label_visibility="collapsed",
            key=f"load_raw_text_{trace_idx}",
        )
    else:
        st.info(t("ingestion_traces.no_preview"))


def _render_split_stage(data: Dict[str, Any], *, trace_idx: int = 0) -> None:
    """Render Split stage: chunk list with texts."""
    c1, c2 = st.columns(2)
    with c1:
        st.metric(t("ingestion_traces.chunks"), data.get("chunk_count", 0))
    with c2:
        st.metric(
            t("ingestion_traces.avg_size"),
            t("common.chars", count=data.get("avg_chunk_size", 0)),
        )

    chunks = data.get("chunks", [])
    if chunks:
        st.markdown(t("ingestion_traces.chunks_after_split"))
        for i, chunk in enumerate(chunks):
            char_len = chunk.get("char_len", 0)
            chunk_id = chunk.get("chunk_id", "")
            text = chunk.get("text", "")
            header = (
                f"📝 {t('common.chunk_label', index=i + 1)} — "
                f"`{chunk_id[:20]}` — {t('common.chars', count=char_len)}"
            )
            with st.expander(header, expanded=(i < 2)):
                st.text_area(
                    f"split_{i}",
                    value=text,
                    height=max(100, min(len(text) // 2, 500)),
                    disabled=True,
                    label_visibility="collapsed",
                    key=f"split_{trace_idx}_{i}",
                )
    else:
        st.info(t("ingestion_traces.no_chunk_text"))


def _render_transform_stage(data: Dict[str, Any], *, trace_idx: int = 0) -> None:
    """Render Transform stage: before/after refinement + enrichment metadata."""
    # Summary metrics
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(
            t("ingestion_traces.refined_llm_rule"),
            f"{data.get('refined_by_llm', 0)} / {data.get('refined_by_rule', 0)}",
        )
    with c2:
        st.metric(
            t("ingestion_traces.enriched_llm_rule"),
            f"{data.get('enriched_by_llm', 0)} / {data.get('enriched_by_rule', 0)}",
        )
    with c3:
        st.metric(t("ingestion_traces.captioned"), data.get("captioned_chunks", 0))

    chunks = data.get("chunks", [])
    if chunks:
        st.markdown(t("ingestion_traces.per_chunk_transform"))
        for i, chunk in enumerate(chunks):
            chunk_id = chunk.get("chunk_id", "")
            refined_by = chunk.get("refined_by", "")
            enriched_by = chunk.get("enriched_by", "")
            title = chunk.get("title", "")
            tags = chunk.get("tags", [])
            summary = chunk.get("summary", "")
            text_before = chunk.get("text_before", "")
            text_after = chunk.get("text_after", "")

            badge_parts = []
            if refined_by:
                badge_parts.append(f"refined:`{refined_by}`")
            if enriched_by:
                badge_parts.append(f"enriched:`{enriched_by}`")
            badges = " · ".join(badge_parts)

            header = (
                f"🔄 {t('common.chunk_label', index=i + 1)} — "
                f"`{chunk_id[:20]}` — {badges}"
            )
            with st.expander(header, expanded=(i == 0)):
                # Metadata from enrichment
                if title or tags or summary:
                    st.markdown(t("ingestion_traces.enriched_metadata"))
                    meta_cols = st.columns(3)
                    with meta_cols[0]:
                        st.markdown(
                            t("ingestion_traces.title_label", value=title)
                            if title
                            else t("ingestion_traces.no_title")
                        )
                    with meta_cols[1]:
                        if tags:
                            st.markdown(
                                t(
                                    "ingestion_traces.tags_label",
                                    value=", ".join(f"`{tag}`" for tag in tags),
                                )
                            )
                        else:
                            st.markdown(t("ingestion_traces.no_tags"))
                    with meta_cols[2]:
                        if summary:
                            st.markdown(
                                t("ingestion_traces.summary_label", value=summary)
                            )

                # Before / After text comparison
                if text_before or text_after:
                    st.markdown(t("ingestion_traces.text_comparison"))
                    # Compute a uniform height so both sides match
                    _max_len = max(len(text_before or ""), len(text_after or ""))
                    _h = max(150, min(_max_len // 2, 600))
                    col_before, col_after = st.columns(2)
                    with col_before:
                        st.markdown(t("ingestion_traces.before_refinement"))
                        st.text_area(
                            f"before_{i}",
                            value=text_before
                            if text_before
                            else t("common.empty_placeholder"),
                            height=_h,
                            disabled=True,
                            label_visibility="collapsed",
                            key=f"transform_before_{trace_idx}_{i}",
                        )
                    with col_after:
                        st.markdown(t("ingestion_traces.after_refinement"))
                        st.text_area(
                            f"after_{i}",
                            value=text_after
                            if text_after
                            else t("common.empty_placeholder"),
                            height=_h,
                            disabled=True,
                            label_visibility="collapsed",
                            key=f"transform_after_{trace_idx}_{i}",
                        )
    else:
        st.info(t("ingestion_traces.no_transform_data"))


def _render_embed_stage(data: Dict[str, Any]) -> None:
    """Render Embed stage: dual-path Dense + Sparse encoding details."""
    # ── Overview metrics ──
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(t("ingestion_traces.dense_vectors"), data.get("dense_vector_count", 0))
    with c2:
        st.metric(t("ingestion_traces.dimension"), data.get("dense_dimension", 0))
    with c3:
        st.metric(t("ingestion_traces.sparse_docs"), data.get("sparse_doc_count", 0))
    with c4:
        st.metric(t("common.method"), data.get("method", "—"))

    chunks = data.get("chunks", [])
    if not chunks:
        st.info(t("ingestion_traces.no_encoding_data"))
        return

    # ── Dual-path per-chunk table ──
    st.markdown("---")
    dense_tab, sparse_tab = st.tabs(
        [t("ingestion_traces.dense_encoding_tab"), t("ingestion_traces.sparse_encoding_tab")]
    )

    with dense_tab:
        st.markdown(t("ingestion_traces.dense_explain"))
        dense_rows = []
        for i, chunk in enumerate(chunks):
            char_len = chunk.get("char_len", 0)
            dense_rows.append({
                t("col.number"): i + 1,
                t("col.chunk_id"): chunk.get("chunk_id", ""),
                t("col.chars"): char_len,
                t("col.est_tokens"): max(1, char_len // 3),
                t("col.dense_dim"): chunk.get(
                    "dense_dim", data.get("dense_dimension", "—")
                ),
            })
        st.table(dense_rows)

    with sparse_tab:
        st.markdown(t("ingestion_traces.sparse_explain"))
        sparse_rows = []
        for i, chunk in enumerate(chunks):
            sparse_rows.append({
                t("col.number"): i + 1,
                t("col.chunk_id"): chunk.get("chunk_id", ""),
                t("col.doc_length_terms"): chunk.get("doc_length", "—"),
                t("col.unique_terms"): chunk.get("unique_terms", "—"),
            })
        st.table(sparse_rows)

        # Top terms per chunk
        for i, chunk in enumerate(chunks):
            top_terms = chunk.get("top_terms", [])
            if top_terms:
                with st.expander(
                    t("ingestion_traces.top_terms_title", index=i + 1),
                    expanded=False,
                ):
                    term_rows = [
                        {
                            t("col.term"): term["term"],
                            t("col.freq"): term["freq"],
                        }
                        for term in top_terms
                    ]
                    st.table(term_rows)


def _render_upsert_stage(data: Dict[str, Any]) -> None:
    """Render Upsert stage: per-store details with chunk mapping."""
    dense_store = data.get("dense_store", {})
    sparse_store = data.get("sparse_store", {})
    image_store = data.get("image_store", {})

    # ── Overview metrics ──
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(
            t("ingestion_traces.dense_vectors"),
            dense_store.get("count", data.get("vector_count", 0)),
        )
    with c2:
        st.metric(
            t("ingestion_traces.sparse_bm25"),
            sparse_store.get("count", data.get("bm25_docs", 0)),
        )
    with c3:
        st.metric(
            t("ingestion_traces.images"),
            image_store.get("count", data.get("images_indexed", 0)),
        )

    # ── Dense store details ──
    if dense_store:
        with st.expander(t("ingestion_traces.dense_store"), expanded=True):
            dc1, dc2 = st.columns(2)
            with dc1:
                st.markdown(f"**Backend:** `{dense_store.get('backend', '—')}`")
                st.markdown(f"**Collection:** `{dense_store.get('collection', '—')}`")
            with dc2:
                st.markdown(f"**Path:** `{dense_store.get('path', '—')}`")
                st.markdown(f"**Vectors:** {dense_store.get('count', 0)}")

    # ── Sparse store details ──
    if sparse_store:
        with st.expander(t("ingestion_traces.sparse_store"), expanded=True):
            sc1, sc2 = st.columns(2)
            with sc1:
                st.markdown(f"**Backend:** `{sparse_store.get('backend', '—')}`")
                st.markdown(f"**Collection:** `{sparse_store.get('collection', '—')}`")
            with sc2:
                st.markdown(f"**Path:** `{sparse_store.get('path', '—')}`")
                st.markdown(f"**Documents:** {sparse_store.get('count', 0)}")

    # ── Image store details ──
    if image_store and image_store.get("count", 0) > 0:
        with st.expander(
            t("ingestion_traces.image_store", count=image_store.get("count", 0)),
            expanded=True,
        ):
            st.markdown(f"**Backend:** `{image_store.get('backend', '—')}`")
            imgs = image_store.get("images", [])
            if imgs:
                img_rows = [
                    {
                        "Image ID": img.get("image_id", ""),
                        "Page": img.get("page", 0),
                        "File": img.get("file_path", ""),
                        "Doc Hash": img.get("doc_hash", "")[:16] + "…",
                    }
                    for img in imgs
                ]
                st.table(img_rows)

    # ── Chunk → Vector ID mapping ──
    chunk_mapping = data.get("chunk_mapping", [])
    if chunk_mapping:
        with st.expander(
            t("ingestion_traces.chunk_mapping", count=len(chunk_mapping)),
            expanded=False,
        ):
            mapping_rows = [
                {
                    "#": i + 1,
                    "Chunk ID": m.get("chunk_id", ""),
                    "Vector ID": m.get("vector_id", ""),
                    "Store": m.get("store", ""),
                    "Collection": m.get("collection", ""),
                }
                for i, m in enumerate(chunk_mapping)
            ]
            st.table(mapping_rows)

    # ── Fallback: legacy format with just vector_ids ──
    if not chunk_mapping and not dense_store:
        vector_ids = data.get("vector_ids", [])
        if vector_ids:
            with st.expander(t("ingestion_traces.vector_ids"), expanded=False):
                for vid in vector_ids:
                    st.code(vid, language=None)
