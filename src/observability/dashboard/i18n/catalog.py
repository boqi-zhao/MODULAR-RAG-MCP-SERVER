"""Translation catalog for the Modular RAG Dashboard.

The catalog is a flat ``{key: {lang: text}}`` mapping.  Keys are grouped by
the page they belong to (``nav.*``, ``overview.*``, ``common.*`` …) so the
UI code reads naturally::

    t("ingestion.start_button")

Adding a language
-----------------
1. Add the language code to :data:`SUPPORTED_LANGS`.
2. Add a display name to :data:`LANG_LABELS`.
3. Add the corresponding entry to every key in :data:`CATALOG`.

:func:`src.observability.dashboard.i18n.translator.t` falls back to
:data:`DEFAULT_LANG` (then to the key itself) when a translation is missing,
so a partially translated catalog never crashes the dashboard.
"""

from __future__ import annotations

# ── Language registry ────────────────────────────────────────────────

DEFAULT_LANG = "zh"
SUPPORTED_LANGS = ("zh", "en")
LANG_LABELS = {"zh": "中文", "en": "English"}


# ── Catalog ──────────────────────────────────────────────────────────
#
# Keys are grouped by page.  Keep the two languages in lock-step.

CATALOG: dict[str, dict[str, str]] = {
    # ── Navigation / app shell ─────────────────────────────────────
    "nav.overview": {"zh": "系统总览", "en": "Overview"},
    "nav.data_browser": {"zh": "数据浏览", "en": "Data Browser"},
    "nav.ingestion_manager": {"zh": "摄取管理", "en": "Ingestion Manager"},
    "nav.ingestion_traces": {"zh": "摄取追踪", "en": "Ingestion Traces"},
    "nav.query_traces": {"zh": "查询追踪", "en": "Query Traces"},
    "nav.evaluation_panel": {"zh": "评估面板", "en": "Evaluation Panel"},
    "app.page_title": {"zh": "Modular RAG 控制台", "en": "Modular RAG Dashboard"},
    "app.sidebar_language": {"zh": "语言 / Language", "en": "Language / 语言"},

    # ── Shared / common strings ────────────────────────────────────
    "common.details": {"zh": "详情", "en": "Details"},
    "common.provider": {"zh": "提供方", "en": "Provider"},
    "common.model": {"zh": "模型", "en": "Model"},
    "common.collection": {"zh": "集合", "en": "集合 (Collection)"},
    "common.chunks": {"zh": "分块", "en": "Chunks"},
    "common.images": {"zh": "图片", "en": "Images"},
    "common.metadata": {"zh": "元数据", "en": "Metadata"},
    "common.content": {"zh": "内容", "en": "Content"},
    "common.method": {"zh": "方法", "en": "Method"},
    "common.source": {"zh": "来源", "en": "Source"},
    "common.stage": {"zh": "阶段", "en": "Stage"},
    "common.elapsed_ms": {"zh": "耗时 (毫秒)", "en": "Elapsed (ms)"},
    "common.empty_placeholder": {"zh": "（空）", "en": "(empty)"},
    "common.no_text_available": {"zh": "_暂无文本_", "en": "_No text available_"},
    "common.chunk_label": {"zh": "分块 {index}", "en": "Chunk {index}"},
    "common.chars": {"zh": "{count} 字符", "en": "{count} chars"},
    "common.file_missing": {"zh": "{name}（文件缺失）", "en": "{name} (file missing)"},

    # ── Overview page ──────────────────────────────────────────────
    "overview.header": {"zh": "📊 系统总览", "en": "📊 System Overview"},
    "overview.component_config": {"zh": "🔧 组件配置", "en": "🔧 Component Configuration"},
    "overview.config_load_failed": {
        "zh": "配置加载失败：{error}",
        "en": "Failed to load configuration: {error}",
    },
    "overview.collection_stats": {"zh": "📁 集合统计", "en": "📁 Collection Statistics"},
    "overview.empty_marker": {"zh": "⚠️ 空", "en": "⚠️ Empty"},
    "overview.no_collections": {
        "zh": "**未找到任何集合，或 ChromaDB 不可用。** 请前往「摄取管理」页面上传并摄取文档。",
        "en": "**No collections found or ChromaDB unavailable.** "
        "Go to the Ingestion Manager page to upload and ingest documents.",
    },
    "overview.trace_stats": {"zh": "📈 追踪统计", "en": "📈 Trace Statistics"},
    "overview.total_traces": {"zh": "追踪总数", "en": "Total traces"},
    "overview.no_traces": {
        "zh": "尚未记录任何追踪。请先执行一次查询或摄取。",
        "en": "No traces recorded yet. Run a query or ingestion first.",
    },

    # ── Data Browser page ──────────────────────────────────────────
    "browser.header": {"zh": "🔍 数据浏览", "en": "🔍 Data Browser"},
    "browser.service_init_failed": {
        "zh": "DataService 初始化失败：{error}",
        "en": "Failed to initialise DataService: {error}",
    },
    "browser.collection": {"zh": "集合", "en": "Collection"},
    "browser.danger_zone": {"zh": "⚠️ 危险操作区", "en": "⚠️ Danger Zone"},
    "browser.danger_warning": {
        "zh": "此操作将**永久删除**所有数据：ChromaDB 集合、BM25 索引、图片、摄取历史与追踪日志。",
        "en": "This will **permanently delete** all data: "
        "ChromaDB collections, BM25 indexes, images, ingestion history, and trace logs.",
    },
    "browser.clear_all": {"zh": "🗑️ 清空所有数据", "en": "🗑️ Clear All Data"},
    "browser.confirm_prompt": {
        "zh": "确认要执行吗？此操作无法撤销！",
        "en": "Are you sure? This action cannot be undone!",
    },
    "browser.confirm_yes": {"zh": "✅ 确认，删除全部", "en": "✅ Yes, delete everything"},
    "browser.cancel": {"zh": "❌ 取消", "en": "❌ Cancel"},
    "browser.cleared_with_errors": {
        "zh": "已清空，但有 {count} 个错误：{errors}",
        "en": "Cleared with {count} error(s): {errors}",
    },
    "browser.cleared_success": {
        "zh": "所有数据已清空！共删除 {count} 个集合。",
        "en": "All data cleared! {count} collection(s) deleted.",
    },
    "browser.docs_load_failed": {
        "zh": "文档加载失败：{error}",
        "en": "Failed to load documents: {error}",
    },
    "browser.no_documents": {
        "zh": "**该集合中没有文档。** 请前往「摄取管理」页面上传并摄取文件，"
        "或在上方下拉框中切换其他集合。",
        "en": "**No documents found in this collection.** "
        "Use the Ingestion Manager page to upload and ingest files, "
        "or select a different collection from the dropdown above.",
    },
    "browser.documents_count": {"zh": "📄 文档（{count}）", "en": "📄 Documents ({count})"},
    "browser.doc_expander": {
        "zh": "📑 {name}  —  {chunks} 个分块 · {images} 张图片",
        "en": "📑 {name}  —  {chunks} chunks · {images} images",
    },
    "browser.hash_label": {"zh": "哈希", "en": "Hash"},
    "browser.processed_at": {"zh": "处理时间", "en": "Processed"},
    "browser.chunks_count": {"zh": "### 📦 分块（{count}）", "en": "### 📦 Chunks ({count})"},
    "browser.chunk_meta": {
        "zh": "**分块 {index}** · `{chunk_id}` · {chars} 字符",
        "en": "**Chunk {index}** · `{chunk_id}` · {chars} chars",
    },
    "browser.no_chunks": {
        "zh": "该文档在向量库中没有分块。",
        "en": "No chunks found in vector store for this document.",
    },
    "browser.images_count": {"zh": "### 🖼️ 图片（{count}）", "en": "### 🖼️ Images ({count})"},

    # ── Ingestion Manager page ─────────────────────────────────────
    "ingestion.header": {"zh": "📥 摄取管理", "en": "📥 Ingestion Manager"},
    "ingestion.upload_section": {"zh": "📤 上传与摄取", "en": "📤 Upload & Ingest"},
    "ingestion.file_label": {"zh": "选择要摄取的文件", "en": "Select a file to ingest"},
    "ingestion.collection_label": {"zh": "集合名称", "en": "Collection"},
    "ingestion.start_button": {"zh": "🚀 开始摄取", "en": "🚀 Start Ingestion"},
    "ingestion.preparing": {"zh": "准备中…", "en": "Preparing…"},
    "ingestion.complete": {"zh": "✅ 完成", "en": "✅ Complete"},
    "ingestion.success": {
        "zh": "已成功将 **{name}** 摄取到集合 **{collection}**。",
        "en": "Successfully ingested **{name}** into collection **{collection}**.",
    },
    "ingestion.failed": {"zh": "摄取失败：{error}", "en": "Ingestion failed: {error}"},
    "ingestion.manage_section": {"zh": "🗑️ 文档管理", "en": "🗑️ Manage Documents"},
    "ingestion.no_documents": {
        "zh": "**尚未摄取任何文档。** 请在上方上传 PDF、TXT、MD 或 DOCX 文件，"
        "然后点击「开始摄取」。",
        "en": "**No documents ingested yet.** "
        'Upload a PDF, TXT, MD, or DOCX file above and click "Start Ingestion" to begin.',
    },
    "ingestion.doc_row": {
        "zh": "**{path}** — 集合：`{collection}` | 分块数：{chunks} | 图片数：{images}",
        "en": "**{path}** — collection: `{collection}` | chunks: {chunks} | images: {images}",
    },
    "ingestion.delete_button": {"zh": "🗑️ 删除", "en": "🗑️ Delete"},
    "ingestion.delete_success": {
        "zh": "已删除：{chunks} 个分块、{images} 张图片。",
        "en": "Deleted: {chunks} chunks, {images} images removed.",
    },
    "ingestion.delete_partial": {
        "zh": "部分删除失败。错误：{errors}",
        "en": "Partial delete. Errors: {errors}",
    },
    "ingestion.delete_failed": {"zh": "删除失败：{error}", "en": "Delete failed: {error}"},
    # Progress stage labels (keys mirror pipeline stage names)
    "ingestion.stage.integrity": {"zh": "🔍 正在校验文件完整性…", "en": "🔍 Checking file integrity…"},
    "ingestion.stage.load": {"zh": "📄 正在加载文档…", "en": "📄 Loading document…"},
    "ingestion.stage.split": {"zh": "✂️ 正在切分文档…", "en": "✂️ Chunking document…"},
    "ingestion.stage.transform": {
        "zh": "🔄 正在转换分块（LLM 精炼 + 元数据增强）…",
        "en": "🔄 Transforming chunks (LLM refine + enrich)…",
    },
    "ingestion.stage.embed": {"zh": "🔢 正在编码向量…", "en": "🔢 Encoding vectors…"},
    "ingestion.stage.upsert": {"zh": "💾 正在写入数据库…", "en": "💾 Storing to database…"},

    # ── Ingestion Traces page ──────────────────────────────────────
    "ingestion_traces.header": {"zh": "🔬 摄取追踪", "en": "🔬 Ingestion Traces"},
    "ingestion_traces.none": {
        "zh": "尚未记录任何摄取追踪。请先执行一次摄取！",
        "en": "No ingestion traces recorded yet. Run an ingestion first!",
    },
    "ingestion_traces.history": {"zh": "📋 追踪历史（{count}）", "en": "📋 Trace History ({count})"},
    "ingestion_traces.pipeline_overview": {"zh": "#### 📊 流程总览", "en": "#### 📊 Pipeline Overview"},
    "ingestion_traces.source_line": {"zh": "来源：`{path}`", "en": "Source: `{path}`"},
    "ingestion_traces.doc_length": {"zh": "文档长度", "en": "Doc Length"},
    "ingestion_traces.chunks": {"zh": "分块数", "en": "Chunks"},
    "ingestion_traces.images": {"zh": "图片数", "en": "Images"},
    "ingestion_traces.vectors": {"zh": "向量数", "en": "Vectors"},
    "ingestion_traces.total_time": {"zh": "总耗时", "en": "Total Time"},
    "ingestion_traces.stage_timings": {"zh": "#### ⏱️ 各阶段耗时", "en": "#### ⏱️ Stage Timings"},
    "ingestion_traces.stage_details": {"zh": "#### 🔍 阶段详情", "en": "#### 🔍 Stage Details"},
    "ingestion_traces.no_stage_details": {"zh": "暂无阶段详情。", "en": "No stage details available."},
    "ingestion_traces.pipeline_incomplete_load": {
        "zh": "**流程不完整 —— 缺少阶段：{names}。** "
        "Load 阶段失败或被跳过。文档可能已损坏或格式不受支持。",
        "en": "**Pipeline incomplete — missing stages: {names}.** "
        "The Load stage failed or was skipped. The document may be corrupted or unsupported.",
    },
    "ingestion_traces.pipeline_incomplete": {
        "zh": "**流程不完整 —— 缺少阶段：{names}。** 处理过程中可能发生错误，请查看日志了解详情。",
        "en": "**Pipeline incomplete — missing stages: {names}.** "
        "An error may have occurred during processing. Check the logs for details.",
    },
    "ingestion_traces.empty_text": {
        "zh": "**Load 阶段产出为空文本。** 该文档可能只有图片，或格式不受支持。",
        "en": "**Load stage produced empty text.** The document may be image-only or in an unsupported format.",
    },
    "ingestion_traces.zero_chunks": {
        "zh": "**Split 阶段产出 0 个分块。** 文档文本可能过短或为空。",
        "en": "**Split stage produced 0 chunks.** The document text may be too short or empty.",
    },
    "ingestion_traces.no_refine": {
        "zh": "**Transform：** 没有分块被精炼。LLM 精炼可能已禁用，或短分块被跳过。",
        "en": "**Transform:** No chunks were refined. LLM refinement may be disabled or skipped for short chunks.",
    },
    "ingestion_traces.zero_vectors": {
        "zh": "**Embed 阶段产出 0 个向量。** 嵌入 API 可能调用失败，请检查 API Key 与 Endpoint。",
        "en": "**Embed stage produced 0 vectors.** Embedding API may have failed. Check API key and endpoint.",
    },
    "ingestion_traces.zero_upsert": {
        "zh": "**Upsert 阶段写入 0 个向量。** 数据库写入可能失败。",
        "en": "**Upsert stage stored 0 vectors.** Database write may have failed.",
    },
    "ingestion_traces.stage_error": {
        "zh": "**{stage} 阶段错误：** {error}",
        "en": "**{stage} stage error:** {error}",
    },
    "ingestion_traces.load_tab": {"zh": "📄 加载", "en": "📄 Load"},
    "ingestion_traces.split_tab": {"zh": "✂️ 切分", "en": "✂️ Split"},
    "ingestion_traces.transform_tab": {"zh": "🔄 转换", "en": "🔄 Transform"},
    "ingestion_traces.embed_tab": {"zh": "🔢 编码", "en": "🔢 Embed"},
    "ingestion_traces.upsert_tab": {"zh": "💾 存储", "en": "💾 Upsert"},
    "ingestion_traces.doc_id": {"zh": "文档 ID", "en": "Doc ID"},
    "ingestion_traces.text_length": {"zh": "文本长度", "en": "Text Length"},
    "ingestion_traces.raw_text": {"zh": "**原始文档文本**", "en": "**Raw Document Text**"},
    "ingestion_traces.no_preview": {"zh": "该追踪未记录文本预览。", "en": "No text preview recorded in this trace."},
    "ingestion_traces.avg_size": {"zh": "平均大小", "en": "Avg Size"},
    "ingestion_traces.chunks_after_split": {"zh": "**切分后的分块**", "en": "**Chunks after splitting**"},
    "ingestion_traces.no_chunk_text": {
        "zh": "未记录分块文本。请重新运行摄取以生成新的追踪。",
        "en": "No chunk text recorded. Re-run ingestion to generate new traces.",
    },
    "ingestion_traces.refined_llm_rule": {"zh": "已精炼（LLM / 规则）", "en": "Refined (LLM / Rule)"},
    "ingestion_traces.enriched_llm_rule": {"zh": "已增强（LLM / 规则）", "en": "Enriched (LLM / Rule)"},
    "ingestion_traces.captioned": {"zh": "已生成图片描述", "en": "Captioned"},
    "ingestion_traces.per_chunk_transform": {
        "zh": "**各分块转换结果**",
        "en": "**Per-chunk transform results**",
    },
    "ingestion_traces.enriched_metadata": {"zh": "**增强后的元数据**", "en": "**Enriched Metadata**"},
    "ingestion_traces.title_label": {"zh": "**标题：** {value}", "en": "**Title:** {value}"},
    "ingestion_traces.no_title": {"zh": "_无标题_", "en": "_No title_"},
    "ingestion_traces.tags_label": {"zh": "**标签：** {value}", "en": "**Tags:** {value}"},
    "ingestion_traces.no_tags": {"zh": "_无标签_", "en": "_No tags_"},
    "ingestion_traces.summary_label": {"zh": "**摘要：** {value}", "en": "**Summary:** {value}"},
    "ingestion_traces.text_comparison": {"zh": "**文本对比**", "en": "**Text Comparison**"},
    "ingestion_traces.before_refinement": {"zh": "*精炼前：*", "en": "*Before refinement:*"},
    "ingestion_traces.after_refinement": {
        "zh": "*精炼 + 增强后：*",
        "en": "*After refinement + enrichment:*",
    },
    "ingestion_traces.no_transform_data": {
        "zh": "未记录各分块转换数据。请重新运行摄取以生成新的追踪。",
        "en": "No per-chunk transform data recorded. Re-run ingestion for new traces.",
    },
    "ingestion_traces.dense_vectors": {"zh": "稠密向量数", "en": "Dense Vectors"},
    "ingestion_traces.dimension": {"zh": "维度", "en": "Dimension"},
    "ingestion_traces.sparse_docs": {"zh": "稀疏文档数", "en": "Sparse Docs"},
    "ingestion_traces.no_encoding_data": {"zh": "未记录分块编码数据。", "en": "No chunk encoding data recorded."},
    "ingestion_traces.dense_encoding_tab": {"zh": "🟦 稠密编码", "en": "🟦 Dense Encoding"},
    "ingestion_traces.sparse_encoding_tab": {"zh": "🟨 稀疏编码（BM25）", "en": "🟨 Sparse Encoding (BM25)"},
    "ingestion_traces.dense_explain": {
        "zh": "每个分块 → 通过嵌入模型生成 **浮点向量**（例如 `text-embedding-ada-002`）",
        "en": "Each chunk → **float vector** via embedding model (e.g. `text-embedding-ada-002`)",
    },
    "ingestion_traces.sparse_explain": {
        "zh": "每个分块 → 生成 **词频统计** 用于 BM25 索引",
        "en": "Each chunk → **term frequency stats** for BM25 indexing",
    },
    "ingestion_traces.top_terms_title": {
        "zh": "🔤 分块 {index} — 高频词",
        "en": "🔤 Chunk {index} — Top Terms",
    },
    "ingestion_traces.dense_store": {"zh": "🟦 稠密向量库（ChromaDB）", "en": "🟦 Dense Vector Store (ChromaDB)"},
    "ingestion_traces.sparse_store": {"zh": "🟨 稀疏索引（BM25）", "en": "🟨 Sparse Index (BM25)"},
    "ingestion_traces.sparse_bm25": {"zh": "稀疏索引（BM25）", "en": "Sparse (BM25)"},
    "ingestion_traces.image_store": {"zh": "🖼️ 图片存储（{count} 张）", "en": "🖼️ Image Storage ({count} images)"},
    "ingestion_traces.chunk_mapping": {
        "zh": "🔗 分块 → 向量映射（{count} 条）",
        "en": "🔗 Chunk → Vector Mapping ({count} entries)",
    },
    "ingestion_traces.vector_ids": {"zh": "向量 ID", "en": "Vector IDs"},
    # Upsert detail field labels
    "field.backend": {"zh": "后端", "en": "Backend"},
    "field.path": {"zh": "路径", "en": "Path"},
    "field.vectors": {"zh": "向量数", "en": "Vectors"},
    "field.documents": {"zh": "文档数", "en": "Documents"},
    "field.raw_document_text": {"zh": "原始文档文本", "en": "Raw Document Text"},

    # ── Query Traces page ──────────────────────────────────────────
    "query_traces.header": {"zh": "🔎 查询追踪", "en": "🔎 Query Traces"},
    "query_traces.none": {
        "zh": "尚未记录任何查询追踪。请先执行一次查询！",
        "en": "No query traces recorded yet. Run a query first!",
    },
    "query_traces.search_label": {"zh": "按查询关键词搜索", "en": "Search by query keyword"},
    "query_traces.history": {"zh": "📋 查询历史（{count}）", "en": "📋 Query History ({count})"},
    "query_traces.query_heading": {"zh": "#### 💬 查询", "en": "#### 💬 Query"},
    "query_traces.source_label": {"zh": "**来源：** {emoji} `{source}`", "en": "**Source:** {emoji} `{source}`"},
    "query_traces.top_k": {"zh": "**Top-K：** `{value}`", "en": "**Top-K:** `{value}`"},
    "query_traces.collection_label": {
        "zh": "**集合：** `{value}`",
        "en": "**Collection:** `{value}`",
    },
    "query_traces.dense_hits": {"zh": "稠密召回", "en": "Dense Hits"},
    "query_traces.sparse_hits": {"zh": "稀疏召回", "en": "Sparse Hits"},
    "query_traces.fused": {"zh": "融合结果", "en": "Fused"},
    "query_traces.after_rerank": {"zh": "重排后", "en": "After Rerank"},
    "query_traces.total_time": {"zh": "总耗时", "en": "Total Time"},
    "query_traces.stage_timings": {"zh": "#### ⏱️ 各阶段耗时", "en": "#### ⏱️ Stage Timings"},
    "query_traces.stage_details": {"zh": "#### 🔍 阶段详情", "en": "#### 🔍 Stage Details"},
    "query_traces.no_stage_details": {"zh": "暂无阶段详情。", "en": "No stage details available."},
    # Diagnostics
    "query_traces.dense_failed": {"zh": "**稠密检索失败：** {error}", "en": "**Dense Retrieval failed:** {error}"},
    "query_traces.dense_zero": {
        "zh": "稠密检索返回 **0 条结果**。请确认该集合中已索引数据。",
        "en": "Dense Retrieval returned **0 results**. Check if the collection has indexed data.",
    },
    "query_traces.sparse_failed": {"zh": "**稀疏检索失败：** {error}", "en": "**Sparse Retrieval failed:** {error}"},
    "query_traces.sparse_zero": {
        "zh": "稀疏（BM25）检索返回 **0 条结果**。该集合的 BM25 索引可能为空或尚未构建。",
        "en": "Sparse (BM25) Retrieval returned **0 results**. "
        "BM25 index may be empty or not yet built for this collection.",
    },
    "query_traces.fusion_not_recorded": {
        "zh": "两路检索均有结果，但未记录融合阶段。",
        "en": "Fusion stage was not recorded even though both retrievers returned results.",
    },
    "query_traces.fusion_skipped": {
        "zh": "**已跳过融合（RRF）：** 仅 {source} 检索返回了结果。"
        "融合需要稠密与稀疏两路结果才能合并。",
        "en": "**Fusion (RRF) skipped:** only {source} retrieval returned results. "
        "Fusion requires both Dense and Sparse results to merge.",
    },
    "query_traces.rerank_skipped": {
        "zh": "**已跳过重排：** 重排器未启用或未配置。"
        "请在 settings.yaml 中启用 `reranker` 以应用基于 LLM 的重排。",
        "en": "**Rerank skipped:** reranker is not enabled or not configured. "
        "Enable `reranker` in settings.yaml to apply LLM-based reranking.",
    },
    "query_traces.no_results": {
        "zh": "**未找到任何结果。** 集合可能为空，或查询与已索引内容不匹配。请先摄取数据。",
        "en": "**No results found.** The collection may be empty, or the query "
        "doesn't match any indexed content. Try ingesting data first.",
    },
    # Stage tabs
    "query_traces.query_processing_tab": {"zh": "🔤 查询处理", "en": "🔤 Query Processing"},
    "query_traces.dense_tab": {"zh": "🟦 稠密检索", "en": "🟦 Dense Retrieval"},
    "query_traces.sparse_tab": {"zh": "🟨 稀疏检索", "en": "🟨 Sparse Retrieval"},
    "query_traces.fusion_tab": {"zh": "🟩 融合（RRF）", "en": "🟩 Fusion (RRF)"},
    "query_traces.rerank_tab": {"zh": "🟪 重排", "en": "🟪 Rerank"},
    # Stage detail renderers
    "query_traces.original_query": {"zh": "**原始查询**", "en": "**Original Query**"},
    "query_traces.method_label": {"zh": "**方法**", "en": "**Method**"},
    "query_traces.extracted_keywords": {"zh": "**提取的关键词**", "en": "**Extracted Keywords**"},
    "query_traces.no_keywords": {"zh": "未提取到关键词。", "en": "No keywords extracted."},
    "query_traces.keywords_label": {"zh": "关键词数", "en": "Keywords"},
    "query_traces.results_label": {"zh": "结果数", "en": "Results"},
    "query_traces.top_k_requested": {"zh": "**请求的 Top-K：** `{value}`", "en": "**Top-K requested:** `{value}`"},
    "query_traces.no_results_for": {"zh": "未返回{label}结果。", "en": "No {label} results returned."},
    "query_traces.dense_word": {"zh": "稠密", "en": "dense"},
    "query_traces.sparse_word": {"zh": "稀疏", "en": "sparse"},
    "query_traces.input_lists": {"zh": "输入路数", "en": "Input Lists"},
    "query_traces.fused_results": {"zh": "融合结果数", "en": "Fused Results"},
    "query_traces.top_k_label": {"zh": "**Top-K：** `{value}`", "en": "**Top-K:** `{value}`"},
    "query_traces.no_fusion_results": {"zh": "没有融合结果。", "en": "No fusion results."},
    "query_traces.input_label": {"zh": "输入数", "en": "Input"},
    "query_traces.output_label": {"zh": "输出数", "en": "Output"},
    "query_traces.no_rerank_results": {"zh": "没有重排结果。", "en": "No reranked results."},
    "query_traces.score_header": {
        "zh": "{bar} **#{index}** — 得分：`{score}`",
        "en": "{bar} **#{index}** — Score: `{score}`",
    },
    "query_traces.chunk_id_label": {"zh": "分块 ID：`{value}`", "en": "Chunk ID: `{value}`"},
    "query_traces.source_chunk_label": {"zh": "来源：`{value}`", "en": "Source: `{value}`"},
    # Ragas section
    "query_traces.ragas_heading": {"zh": "#### 📏 Ragas 评估", "en": "#### 📏 Ragas Evaluation"},
    "query_traces.ragas_intro": {
        "zh": "RAGAS 需要 **Query + Retrieved Context + Answer** 三要素来评估。"
        "日志中仅包含 Query 和检索到的上下文，请在下方输入实际回答后再运行评估。",
        "en": "RAGAS requires **Query + Retrieved Context + Answer** to evaluate. "
        "The trace only contains the query and retrieved context — "
        "enter the actual answer below before running the evaluation.",
    },
    "query_traces.answer_label": {"zh": "✏️ 系统生成的回答", "en": "✏️ Generated Answer"},
    "query_traces.answer_placeholder": {
        "zh": "请输入系统生成的回答，或粘贴 LLM 的实际输出…",
        "en": "Enter the system's answer, or paste the LLM's actual output…",
    },
    "query_traces.answer_help": {
        "zh": "Ragas 使用 LLM-as-Judge 评估回答质量。"
        "faithfulness 衡量回答是否忠于检索到的上下文，"
        "answer_relevancy 衡量回答与问题的相关性。"
        "如果不填写回答，将无法获得有意义的评估结果。",
        "en": "Ragas evaluates answer quality with LLM-as-Judge. "
        "faithfulness measures whether the answer stays true to the retrieved context; "
        "answer_relevancy measures how relevant the answer is to the question. "
        "Without an answer, the scores will not be meaningful.",
    },
    "query_traces.evaluate_button": {"zh": "📏 运行 Ragas 评估", "en": "📏 Ragas Evaluate"},
    "query_traces.evaluate_help": {
        "zh": "重新执行该查询并使用 Ragas 打分（LLM-as-Judge）",
        "en": "Re-run this query and score with Ragas (LLM-as-Judge)",
    },
    "query_traces.answer_required": {"zh": "⚠️ 请先在上方输入回答内容，再运行 Ragas 评估。", "en": "⚠️ Please enter an answer above before running the Ragas evaluation."},
    "query_traces.evaluate_note": {
        "zh": "使用 Ragas 对 faithfulness、answer relevancy 和 context precision 打分。会调用 LLM，可能需要几秒钟。",
        "en": "Uses Ragas to score faithfulness, answer relevancy, "
        "and context precision. Calls LLM — may take a few seconds.",
    },
    "query_traces.running_eval": {"zh": "正在运行 Ragas 评估…", "en": "Running Ragas evaluation…"},
    "query_traces.no_chunks_retrieved": {
        "zh": "未检索到任何分块 —— 数据是否已索引？",
        "en": "No chunks retrieved — is data indexed?",
    },
    "query_traces.ragas_not_installed": {"zh": "Ragas 未安装：{error}", "en": "Ragas not installed: {error}"},
    "query_traces.eval_failed": {"zh": "❌ 评估失败：{error}", "en": "❌ Evaluation failed: {error}"},
    "query_traces.no_metrics": {"zh": "未返回任何指标。", "en": "No metrics returned."},
    "query_traces.ragas_scores": {"zh": "**📏 Ragas 得分**", "en": "**📏 Ragas Scores**"},

    # ── Evaluation Panel page ──────────────────────────────────────
    "eval.header": {"zh": "📏 评估面板", "en": "📏 Evaluation Panel"},
    "eval.intro": {
        "zh": "基于 **黄金测试集** 运行评估，衡量检索与生成质量。结果包含每个查询的明细与聚合指标。",
        "en": "Run evaluation against a **golden test set** to measure retrieval "
        "and generation quality. Results include per-query details and aggregate metrics.",
    },
    "eval.config_section": {"zh": "⚙️ 配置", "en": "⚙️ Configuration"},
    "eval.backend_label": {"zh": "评估器后端", "en": "Evaluator Backend"},
    "eval.backend_help": {"zh": "选择要使用的评估器后端。", "en": "Select which evaluator backend to use."},
    "eval.custom_notice": {
        "zh": "ℹ️ **Custom 评估器** 尚未完成数据集准备，当前仅为预留接口。"
        "Custom 评估器需要在 Golden Test Set 中填写 `expected_chunk_ids` "
        "作为 ground truth 才能计算 hit_rate / MRR 指标。"
        "目前建议使用 **ragas** 后端进行评估。",
        "en": "ℹ️ **Custom Evaluator** has no prepared dataset yet — it is a placeholder interface. "
        "It needs `expected_chunk_ids` in the Golden Test Set as ground truth "
        "to compute hit_rate / MRR. Using the **ragas** backend is recommended for now.",
    },
    "eval.top_k_label": {"zh": "Top-K", "en": "Top-K"},
    "eval.top_k_help": {"zh": "每个查询检索的分块数量。", "en": "Number of chunks to retrieve per query."},
    "eval.collection_label": {"zh": "集合（可选）", "en": "Collection (optional)"},
    "eval.collection_help": {"zh": "将检索范围限定到指定集合。", "en": "Limit retrieval to a specific collection."},
    "eval.golden_path_label": {"zh": "黄金测试集路径", "en": "Golden Test Set Path"},
    "eval.golden_path_help": {"zh": "golden_test_set.json 文件的路径。", "en": "Path to the golden_test_set.json file."},
    "eval.golden_not_found": {
        "zh": "⚠️ **未找到黄金测试集：** `{path}`。"
        "请创建包含测试查询与预期结果的 JSON 文件，格式参见 "
        "`tests/fixtures/golden_test_set.json`。",
        "en": "⚠️ **Golden test set not found:** `{path}`. "
        "Create a JSON file with test queries and expected results. "
        "See `tests/fixtures/golden_test_set.json` for the format.",
    },
    "eval.answers_section": {"zh": "✏️ 填写回答", "en": "✏️ Provide Answers"},
    "eval.answers_caption": {
        "zh": "**RAGAS 需要 Query + Context + Answer 三要素来评估。**"
        "日志中仅包含 Query 和检索到的上下文（Context），"
        "请为每个测试用例填写实际的系统回答（Answer），"
        "以便获得有意义的 faithfulness 和 answer_relevancy 评分。",
        "en": "**RAGAS needs Query + Context + Answer to evaluate.** "
        "The trace only contains the query and retrieved context. "
        "Fill in the actual system answer for each test case "
        "to get meaningful faithfulness and answer_relevancy scores.",
    },
    "eval.answer_placeholder": {"zh": "请输入该问题对应的系统回答…", "en": "Enter the system answer for this question…"},
    "eval.answer_help": {
        "zh": "Query: {query}\n\n填写 LLM 生成的回答或期望的回答文本。"
        "Ragas 会基于此评估 faithfulness（忠实度）和 answer_relevancy（相关性）。",
        "en": "Query: {query}\n\n"
        "Enter the LLM-generated answer or the expected answer text. "
        "Ragas uses it to score faithfulness and answer_relevancy.",
    },
    "eval.fill_status_partial": {
        "zh": "⚠️ 已填写 {filled}/{total} 个回答。未填写的用例将使用检索片段拼接作为回答（评估结果可能不准确）。",
        "en": "⚠️ {filled}/{total} answers provided. Unfilled cases will use concatenated "
        "retrieved chunks as the answer (results may be inaccurate).",
    },
    "eval.fill_status_done": {"zh": "✅ 所有 {total} 个回答已填写。", "en": "✅ All {total} answers provided."},
    "eval.testcase_load_failed": {"zh": "无法加载测试用例预览：{error}", "en": "Could not load test case preview: {error}"},
    "eval.run_button": {"zh": "▶️ 运行评估", "en": "▶️  Run Evaluation"},
    "eval.loading": {"zh": "正在加载评估器并运行评估…", "en": "Loading evaluator and running evaluation…"},
    "eval.failed": {"zh": "❌ 评估失败：{error}", "en": "❌ Evaluation failed: {error}"},
    "eval.complete": {"zh": "✅ 评估完成！", "en": "✅ Evaluation complete!"},
    "eval.aggregate_metrics": {"zh": "📊 聚合指标", "en": "📊 Aggregate Metrics"},
    "eval.no_aggregate": {"zh": "暂无聚合指标。", "en": "No aggregate metrics available."},
    "eval.aggregate_summary": {
        "zh": "评估器：**{evaluator}** · 查询数：**{count}** · 总耗时：**{elapsed} ms**",
        "en": "Evaluator: **{evaluator}** · Queries: **{count}** · Total time: **{elapsed} ms**",
    },
    "eval.per_query_details": {"zh": "🔍 各查询明细", "en": "🔍 Per-Query Details"},
    "eval.no_per_query": {"zh": "暂无各查询结果。", "en": "No per-query results available."},
    "eval.query_expander": {"zh": "**Q{index}**：{query} — {elapsed} ms — {metrics}", "en": "**Q{index}**: {query} — {elapsed} ms — {metrics}"},
    "eval.no_metrics_short": {"zh": "无指标", "en": "no metrics"},
    "eval.retrieved_chunks": {"zh": "**检索到的分块**（{count}）：", "en": "**Retrieved Chunks** ({count}):"},
    "eval.generated_answer": {"zh": "**生成的回答：**", "en": "**Generated Answer:**"},
    "eval.history_section": {"zh": "📈 评估历史", "en": "📈 Evaluation History"},
    "eval.no_history": {
        "zh": "**暂无评估历史。** 请在上方配置评估器并点击「运行评估」开始。结果将保存在此处以便跨次对比。",
        "en": "**No evaluation history yet.** "
        'Configure the evaluator above and click "Run Evaluation" to start. '
        "Results will be saved here for comparison across runs.",
    },

    # ── Table column headers (kept as data keys where used inline) ──
    "col.stage": {"zh": "阶段", "en": "Stage"},
    "col.elapsed_ms": {"zh": "耗时 (毫秒)", "en": "Elapsed (ms)"},
    "col.chunk_id": {"zh": "分块 ID", "en": "Chunk ID"},
    "col.chars": {"zh": "字符数", "en": "Chars"},
    "col.est_tokens": {"zh": "预估 Token 数", "en": "Est. Tokens"},
    "col.dense_dim": {"zh": "稠密维度", "en": "Dense Dim"},
    "col.doc_length_terms": {"zh": "文档长度（词数）", "en": "Doc Length (terms)"},
    "col.unique_terms": {"zh": "唯一词数", "en": "Unique Terms"},
    "col.term": {"zh": "词项", "en": "Term"},
    "col.freq": {"zh": "频次", "en": "Freq"},
    "col.image_id": {"zh": "图片 ID", "en": "Image ID"},
    "col.page": {"zh": "页码", "en": "Page"},
    "col.file": {"zh": "文件", "en": "File"},
    "col.doc_hash": {"zh": "文档哈希", "en": "Doc Hash"},
    "col.vector_id": {"zh": "向量 ID", "en": "Vector ID"},
    "col.store": {"zh": "存储", "en": "Store"},
    "col.collection": {"zh": "集合", "en": "Collection"},
    "col.number": {"zh": "序号", "en": "#"},
    "col.timestamp": {"zh": "时间", "en": "Timestamp"},
    "col.evaluator": {"zh": "评估器", "en": "Evaluator"},
    "col.queries": {"zh": "查询数", "en": "Queries"},
    "col.time_ms": {"zh": "耗时 (ms)", "en": "Time (ms)"},
}
