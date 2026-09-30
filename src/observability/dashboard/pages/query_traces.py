"""Query Traces page – browse query trace history with stage waterfall.

Layout:
1. Optional keyword search filter
2. Trace list (reverse-chronological, filtered to trace_type=="query")
3. Detail view: stage waterfall + Dense vs Sparse comparison + Rerank delta
4. Per-trace Ragas evaluation button (LLM-as-Judge scoring)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import streamlit as st

from src.observability.dashboard.i18n import t
from src.observability.dashboard.services.trace_service import TraceService

logger = logging.getLogger(__name__)


def render() -> None:
    """Render the Query Traces page."""
    st.header(t("query_traces.header"))

    svc = TraceService()
    traces = svc.list_traces(trace_type="query")

    if not traces:
        st.info(t("query_traces.none"))
        return

    # ── Keyword filter ─────────────────────────────────────────────
    keyword = st.text_input(
        t("query_traces.search_label"),
        value="",
        key="qt_keyword",
    )
    if keyword.strip():
        kw = keyword.strip().lower()
        traces = [
            t
            for t in traces
            if kw in str(t.get("metadata", {})).lower()
            or kw in str(t.get("stages", [])).lower()
        ]

    st.subheader(t("query_traces.history", count=len(traces)))

    for idx, trace in enumerate(traces):
        trace_id = trace.get("trace_id", "unknown")
        started = trace.get("started_at", "—")
        total_ms = trace.get("elapsed_ms")
        total_label = f"{total_ms:.0f} ms" if total_ms is not None else "—"
        meta = trace.get("metadata", {})
        query_text = meta.get("query", "")
        source = meta.get("source", "unknown")

        # ── Expander title: show query text ────────────────────
        query_preview = (
            query_text[:40] + "…" if len(query_text) > 40 else query_text
        ) if query_text else "—"
        expander_title = (
            f"🔍 \"{query_preview}\"  ·  {total_label}  ·  {started[:19]}"
        )

        with st.expander(expander_title, expanded=(idx == 0)):
            # ── 1. Query overview ──────────────────────────────
            st.markdown(t("query_traces.query_heading"))
            col_q, col_meta = st.columns([3, 1])
            with col_q:
                st.markdown(f"> {query_text}")
            with col_meta:
                source_emoji = "🤖" if source == "mcp" else "📡"
                st.markdown(
                    t("query_traces.source_label", emoji=source_emoji, source=source)
                )
                st.markdown(t("query_traces.top_k", value=meta.get("top_k", "—")))
                st.markdown(
                    t("query_traces.collection_label", value=meta.get("collection", "—"))
                )

            st.divider()

            # ── 2. Overview metrics ────────────────────────────
            timings = svc.get_stage_timings(trace)
            stages_by_name = {item["stage_name"]: item for item in timings}

            dense_d = (stages_by_name.get("dense_retrieval", {}).get("data") or {})
            sparse_d = (stages_by_name.get("sparse_retrieval", {}).get("data") or {})
            fusion_d = (stages_by_name.get("fusion", {}).get("data") or {})
            rerank_d = (stages_by_name.get("rerank", {}).get("data") or {})

            dense_count = dense_d.get("result_count", 0)
            sparse_count = sparse_d.get("result_count", 0)
            fusion_count = fusion_d.get("result_count", 0)
            rerank_count = rerank_d.get("output_count", 0)

            rc1, rc2, rc3, rc4, rc5 = st.columns(5)
            with rc1:
                st.metric(t("query_traces.dense_hits"), dense_count)
            with rc2:
                st.metric(t("query_traces.sparse_hits"), sparse_count)
            with rc3:
                st.metric(t("query_traces.fused"), fusion_count or (dense_count + sparse_count))
            with rc4:
                st.metric(t("query_traces.after_rerank"), rerank_count if rerank_d else "—")
            with rc5:
                st.metric(t("query_traces.total_time"), total_label)

            # ── Diagnostic hints ───────────────────────────────
            _render_diagnostics(
                stages_by_name, dense_d, sparse_d, fusion_d, rerank_d,
                dense_count, sparse_count,
            )

            st.divider()

            # ── 3. Stage timing waterfall ──────────────────────
            main_stage_names = ("query_processing", "dense_retrieval", "sparse_retrieval", "fusion", "rerank")
            main_timings = [
                stage for stage in timings if stage["stage_name"] in main_stage_names
            ]
            if main_timings:
                st.markdown(t("query_traces.stage_timings"))
                chart_data = {
                    stage["stage_name"]: stage["elapsed_ms"] for stage in main_timings
                }
                st.bar_chart(chart_data, horizontal=True)
                st.table([
                    {
                        t("col.stage"): stage["stage_name"],
                        t("col.elapsed_ms"): round(stage["elapsed_ms"], 2),
                    }
                    for stage in main_timings
                ])

            st.divider()

            # ── 4. Per-stage detail tabs ───────────────────────
            st.markdown(t("query_traces.stage_details"))

            _TAB_KEYS = {
                "query_processing": "query_traces.query_processing_tab",
                "dense_retrieval": "query_traces.dense_tab",
                "sparse_retrieval": "query_traces.sparse_tab",
                "fusion": "query_traces.fusion_tab",
                "rerank": "query_traces.rerank_tab",
            }
            tab_defs = [
                (t(label_key), stage_key)
                for stage_key, label_key in _TAB_KEYS.items()
                if stage_key in stages_by_name
            ]

            if tab_defs:
                tabs = st.tabs([label for label, _ in tab_defs])
                for tab, (label, key) in zip(tabs, tab_defs):
                    with tab:
                        stage = stages_by_name[key]
                        data = stage.get("data", {})
                        elapsed = stage.get("elapsed_ms")
                        if elapsed is not None:
                            st.caption(f"⏱️ {elapsed:.1f} ms")

                        if key == "query_processing":
                            _render_query_processing_stage(data)
                        elif key == "dense_retrieval":
                            _render_retrieval_stage(
                                data, t("query_traces.dense_word"), trace_idx=idx
                            )
                        elif key == "sparse_retrieval":
                            _render_retrieval_stage(
                                data, t("query_traces.sparse_word"), trace_idx=idx
                            )
                        elif key == "fusion":
                            _render_fusion_stage(data, trace_idx=idx)
                        elif key == "rerank":
                            _render_rerank_stage(data, trace_idx=idx)
            else:
                st.info(t("query_traces.no_stage_details"))

            # ── 5. Ragas Evaluate button ───────────────────────
            _render_evaluate_button(trace, idx)


def _render_diagnostics(
    stages_by_name: Dict[str, Any],
    dense_d: Dict[str, Any],
    sparse_d: Dict[str, Any],
    fusion_d: Dict[str, Any],
    rerank_d: Dict[str, Any],
    dense_count: int,
    sparse_count: int,
) -> None:
    """Render diagnostic hints about missing or errored pipeline stages."""
    hints: list = []

    # Dense errors
    dense_err = dense_d.get("error", "")
    if dense_err:
        hints.append(("error", t("query_traces.dense_failed", error=dense_err)))
    elif dense_count == 0 and "dense_retrieval" in stages_by_name:
        hints.append(("warning", t("query_traces.dense_zero")))

    # Sparse errors / empty
    sparse_err = sparse_d.get("error", "")
    if sparse_err:
        hints.append(("error", t("query_traces.sparse_failed", error=sparse_err)))
    elif sparse_count == 0 and "sparse_retrieval" in stages_by_name:
        hints.append(("warning", t("query_traces.sparse_zero")))

    # Fusion missing
    if "fusion" not in stages_by_name:
        if dense_count > 0 and sparse_count > 0:
            hints.append(("info", t("query_traces.fusion_not_recorded")))
        elif dense_count == 0 or sparse_count == 0:
            only_source = (
                t("query_traces.dense_word") if dense_count > 0
                else (t("query_traces.sparse_word") if sparse_count > 0 else "—")
            )
            hints.append((
                "info",
                t("query_traces.fusion_skipped", source=only_source),
            ))

    # Rerank missing
    if "rerank" not in stages_by_name:
        if dense_count > 0 or sparse_count > 0:
            hints.append(("info", t("query_traces.rerank_skipped")))

    # All results empty
    if dense_count == 0 and sparse_count == 0:
        hints.append(("warning", t("query_traces.no_results")))

    # Render hints
    for level, msg in hints:
        if level == "error":
            st.error(msg)
        elif level == "warning":
            st.warning(msg)
        else:
            st.info(msg)


def _render_evaluate_button(trace: Dict[str, Any], idx: int) -> None:
    """Render a Ragas evaluate button for a single query trace.

    Re-runs retrieval for the stored query and evaluates with
    RagasEvaluator (LLM-as-Judge).  Only works when query text
    is available in trace metadata.
    """
    meta = trace.get("metadata", {})
    query = meta.get("query", "")
    if not query:
        return

    st.divider()
    st.markdown(t("query_traces.ragas_heading"))
    st.caption(t("query_traces.ragas_intro"))

    # Answer input box — user provides the actual generated answer
    answer_key = f"eval_answer_{idx}"
    user_answer = st.text_area(
        t("query_traces.answer_label"),
        value=st.session_state.get(answer_key, ""),
        height=120,
        key=answer_key,
        placeholder=t("query_traces.answer_placeholder"),
        help=t("query_traces.answer_help"),
    )

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        clicked = st.button(
            t("query_traces.evaluate_button"),
            key=f"eval_trace_{idx}",
            help=t("query_traces.evaluate_help"),
            disabled=not user_answer.strip(),
        )
    with col_info:
        if not user_answer.strip():
            st.warning(t("query_traces.answer_required"))
        else:
            st.caption(t("query_traces.evaluate_note"))

    # Show previous result from session state
    result_key = f"eval_result_{idx}"
    if result_key in st.session_state and not clicked:
        _display_eval_metrics(st.session_state[result_key])

    if clicked:
        with st.spinner(t("query_traces.running_eval")):
            result = _evaluate_single_trace(query, meta, user_answer=user_answer.strip())
        st.session_state[result_key] = result
        _display_eval_metrics(result)


def _evaluate_single_trace(
    query: str,
    meta: Dict[str, Any],
    user_answer: Optional[str] = None,
) -> Dict[str, Any]:
    """Re-run retrieval and evaluate a single query with Ragas.

    Returns dict with 'metrics' (score dict) or 'error' (str).
    """
    try:
        from dataclasses import replace as dc_replace

        from src.core.settings import load_settings, EvaluationSettings
        from src.libs.evaluator.evaluator_factory import EvaluatorFactory

        settings = load_settings()

        # Override evaluation settings to force Ragas (frozen dataclass, use replace)
        ragas_eval = EvaluationSettings(
            enabled=True,
            provider="ragas",
            metrics=["faithfulness", "answer_relevancy", "context_precision"],
        )
        settings = dc_replace(settings, evaluation=ragas_eval)
        evaluator = EvaluatorFactory.create(settings)

        # Re-run retrieval
        collection = meta.get("collection", "default")
        top_k = meta.get("top_k", 10)
        chunks = _retrieve_chunks(settings, query, top_k, collection)

        if not chunks:
            return {"error": t("query_traces.no_chunks_retrieved")}

        # Use user-provided answer; fall back to chunk concatenation only
        # as a last resort (produces less meaningful RAGAS scores).
        if user_answer:
            answer = user_answer
        else:
            _MAX_ANSWER_CHARS = 1500
            texts = []
            for c in chunks:
                if hasattr(c, "text"):
                    texts.append(c.text)
                elif isinstance(c, dict):
                    texts.append(c.get("text", str(c)))
                else:
                    texts.append(str(c))
            answer = " ".join(texts[:3])
            if len(answer) > _MAX_ANSWER_CHARS:
                answer = answer[:_MAX_ANSWER_CHARS]

        # Evaluate
        metrics = evaluator.evaluate(
            query=query,
            retrieved_chunks=chunks,
            generated_answer=answer,
        )
        return {"metrics": metrics, "answer_used": answer}

    except ImportError as exc:
        return {"error": t("query_traces.ragas_not_installed", error=exc)}
    except Exception as exc:
        logger.exception("Ragas evaluation failed")
        return {"error": str(exc)}


def _retrieve_chunks(
    settings: Any,
    query: str,
    top_k: int,
    collection: str,
) -> list:
    """Re-run HybridSearch + Rerank to retrieve chunks for evaluation."""
    try:
        from src.core.query_engine.hybrid_search import create_hybrid_search
        from src.core.query_engine.query_processor import QueryProcessor
        from src.core.query_engine.dense_retriever import create_dense_retriever
        from src.core.query_engine.sparse_retriever import create_sparse_retriever
        from src.core.query_engine.reranker import create_core_reranker
        from src.ingestion.storage.bm25_indexer import BM25Indexer
        from src.libs.embedding.embedding_factory import EmbeddingFactory
        from src.libs.vector_store.vector_store_factory import VectorStoreFactory

        vector_store = VectorStoreFactory.create(
            settings, collection_name=collection,
        )
        embedding_client = EmbeddingFactory.create(settings)
        dense_retriever = create_dense_retriever(
            settings=settings,
            embedding_client=embedding_client,
            vector_store=vector_store,
        )
        from src.core.settings import resolve_path
        bm25_indexer = BM25Indexer(index_dir=str(resolve_path(f"data/db/bm25/{collection}")))
        sparse_retriever = create_sparse_retriever(
            settings=settings,
            bm25_indexer=bm25_indexer,
            vector_store=vector_store,
        )
        sparse_retriever.default_collection = collection
        query_processor = QueryProcessor()
        hybrid_search = create_hybrid_search(
            settings=settings,
            query_processor=query_processor,
            dense_retriever=dense_retriever,
            sparse_retriever=sparse_retriever,
        )

        # Retrieve more candidates if rerank is enabled
        reranker = create_core_reranker(settings=settings)
        initial_top_k = top_k * 2 if reranker.is_enabled else top_k

        results = hybrid_search.search(query=query, top_k=initial_top_k)
        results = results if isinstance(results, list) else results.results

        # Apply reranking if enabled
        if reranker.is_enabled and results:
            rerank_result = reranker.rerank(query=query, results=results, top_k=top_k)
            results = rerank_result.results

        return results
    except Exception as exc:
        logger.warning("Retrieval for evaluation failed: %s", exc)
        return []


def _display_eval_metrics(result: Dict[str, Any]) -> None:
    """Display evaluation result (metrics or error)."""
    if "error" in result:
        st.error(t("query_traces.eval_failed", error=result["error"]))
        return

    metrics = result.get("metrics", {})
    if not metrics:
        st.warning(t("query_traces.no_metrics"))
        return

    st.markdown(t("query_traces.ragas_scores"))
    cols = st.columns(min(len(metrics), 4))
    for i, (name, value) in enumerate(sorted(metrics.items())):
        with cols[i % len(cols)]:
            st.metric(
                label=name.replace("_", " ").title(),
                value=f"{value:.4f}",
            )


def _extract_pipeline_chunks(
    timings: List[Dict[str, Any]],
    meta: Dict[str, Any],
) -> Dict[str, List[Dict[str, Any]]]:
    """Extract chunk lists from each pipeline stage."""
    result: Dict[str, List[Dict[str, Any]]] = {}
    for stage in timings:
        name = stage.get("stage_name", "")
        data = stage.get("data") or {}
        chunks = data.get("chunks")
        if chunks and isinstance(chunks, list):
            result[name] = chunks
    final = meta.get("final_results") or meta.get("results")
    if final and isinstance(final, list):
        result["final"] = final
    return result


# ═══════════════════════════════════════════════════════════════
# Per-stage renderers
# ═══════════════════════════════════════════════════════════════

def _render_query_processing_stage(data: Dict[str, Any]) -> None:
    """Render Query Processing stage: original query → keywords."""
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(t("query_traces.original_query"))
        st.info(data.get("original_query", "—"))
    with c2:
        st.markdown(t("query_traces.method_label"))
        st.code(data.get("method", "—"))

    keywords = data.get("keywords", [])
    if keywords:
        st.markdown(t("query_traces.extracted_keywords"))
        st.markdown(" · ".join(f"`{kw}`" for kw in keywords))
    else:
        st.warning(t("query_traces.no_keywords"))


def _render_retrieval_stage(data: Dict[str, Any], label: str, *, trace_idx: int = 0) -> None:
    """Render Dense or Sparse retrieval stage: method, counts, chunk list."""
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(t("common.method"), data.get("method", "—"))
    with c2:
        extra = data.get("provider", data.get("keyword_count", "—"))
        extra_label = (
            t("common.provider") if "provider" in data
            else t("query_traces.keywords_label")
        )
        st.metric(extra_label, extra)
    with c3:
        st.metric(t("query_traces.results_label"), data.get("result_count", 0))

    st.markdown(t("query_traces.top_k_requested", value=data.get("top_k", "—")))

    chunks = data.get("chunks", [])
    if chunks:
        _render_chunk_list(chunks, prefix=f"{label.lower().replace(' ', '_')}_chunk_{trace_idx}")
    else:
        st.info(t("query_traces.no_results_for", label=label))


def _render_fusion_stage(data: Dict[str, Any], *, trace_idx: int = 0) -> None:
    """Render Fusion (RRF) stage: input lists, fused result count, chunk list."""
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(t("common.method"), data.get("method", "rrf"))
    with c2:
        st.metric(t("query_traces.input_lists"), data.get("input_lists", "—"))
    with c3:
        st.metric(t("query_traces.fused_results"), data.get("result_count", 0))

    st.markdown(t("query_traces.top_k_label", value=data.get("top_k", "—")))

    chunks = data.get("chunks", [])
    if chunks:
        _render_chunk_list(chunks, prefix=f"fusion_chunk_{trace_idx}")
    else:
        st.info(t("query_traces.no_fusion_results"))


def _render_rerank_stage(data: Dict[str, Any], *, trace_idx: int = 0) -> None:
    """Render Rerank stage: method, input/output counts, reranked chunk list."""
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(t("common.method"), data.get("method", "—"))
    with c2:
        st.metric(t("common.provider"), data.get("provider", "—"))
    with c3:
        st.metric(t("query_traces.input_label"), data.get("input_count", "—"))
    with c4:
        st.metric(t("query_traces.output_label"), data.get("output_count", "—"))

    chunks = data.get("chunks", [])
    if chunks:
        _render_chunk_list(chunks, prefix=f"rerank_chunk_{trace_idx}")
    else:
        st.info(t("query_traces.no_rerank_results"))


def _render_chunk_list(chunks: List[Dict[str, Any]], prefix: str = "chunk") -> None:
    """Render a list of chunk dicts as a compact, readable table with expandable text."""
    for ci, chunk in enumerate(chunks):
        score = chunk.get("score", 0)
        text = chunk.get("text", "")
        chunk_id = chunk.get("chunk_id", "")
        source = chunk.get("source", "")
        title = chunk.get("title", "")

        # Colour-coded score indicator
        if score >= 0.8:
            score_bar = "🟢"
        elif score >= 0.5:
            score_bar = "🟡"
        else:
            score_bar = "🔴"

        header = t(
            "query_traces.score_header",
            bar=score_bar,
            index=ci + 1,
            score=f"{score:.4f}",
        )
        if title:
            header += f" — {title}"

        with st.expander(header, expanded=False):
            cols = st.columns([2, 3])
            with cols[0]:
                st.caption(t("query_traces.chunk_id_label", value=chunk_id))
            with cols[1]:
                if source:
                    st.caption(t("query_traces.source_chunk_label", value=source))
            # Show chunk text (scrollable)
            if text:
                st.text_area(
                    f"{prefix}_{ci}",
                    value=text,
                    height=max(80, min(len(text) // 2, 400)),
                    disabled=True,
                    label_visibility="collapsed",
                )
            else:
                st.caption(t("common.no_text_available"))


def _find_stage(timings, name):
    """Find a stage dict by name, or None."""
    for item in timings:
        if item["stage_name"] == name:
            return item
    return None
