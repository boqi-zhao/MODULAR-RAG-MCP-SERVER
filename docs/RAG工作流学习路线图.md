# RAG 工作流学习路线图（基于 Modular RAG MCP Server）

> 用途：按 **RAG 技术链路** 逐段研究本项目，每一段都给出「原理 → 项目怎么做的 → 源码在哪 → 关键函数 → 自检问题」。
> 本图对照 `DEV_SPEC.md`（3214 行）与 `src/` 实际代码核对生成。
>
> ⚠️ **先读这一条**：DEV_SPEC 声称 68/68 任务 100% 完成，但 `README.md` FAQ 明确承认
> **Cross-Encoder Reranker** 与 **Custom Evaluator** 两个模块"框架已有、未测试"。
> 凡涉及这两处，务必先实跑验证，不要直接采信文档。

---

## 全局视图

RAG 工作流共 **7 条主线**，分两大域：

```
【离线摄取域】
  ① 数据预处理 (Loader)           PDF → canonical Markdown + metadata
  ② 分割策略 (Splitter)           Markdown → 语义 Chunk
  ③ 增强与向量化 (Transform+Embed) LLM 重组 / 元数据 / 图转文 → 双路向量
  ④ 存储索引 (Upsert)             幂等 All-in-One 持久化

【在线查询域】
  ⑤ 查询理解与召回 (Query+Hybrid)  预处理 → 并行双路 → RRF 融合
  ⑥ 精排与过滤 (Filter+Rerank)     前置/后置过滤 → 可插拔精排 → 回退
  ⑦ 评测与可观测 (Eval+Trace)      双链路 Trace + Golden Set 回归

【横切地基】
  ⚙️ 可插拔架构 (Libs Factory)      六大组件抽象接口 + 工厂 + YAML 配置
  🔌 MCP 服务层                    把以上能力暴露给 Copilot / Claude
```

**依赖关系**：⚙️ 是全局地基（每段都从它取组件）；①→②→③→④ 顺序不可逆；⑤→⑥ 顺序不可逆；⑦ 横切全链路。

---

## ⚙️ 横切地基：可插拔架构

**先学这个**，否则后面每一段都会看到 `xxx_factory.py` 却不知道在干嘛。

**原理**：六大组件（LLM / Embedding / Splitter / VectorStore / Reranker / Evaluator）各自定义抽象基类，具体实现注册进工厂，由 `config/settings.yaml` 决定运行时实例化哪个。目标是**改配置不改代码**。

**源码**：`src/libs/`

| 组件 | 抽象接口 | 实现 | 工厂 |
|------|---------|------|------|
| LLM | `llm/base_llm.py` | `openai_llm.py` / `azure_llm.py` / `deepseek_llm.py` / `ollama_llm.py` | `llm_factory.py` |
| Vision LLM | `llm/base_vision_llm.py` | `openai_vision_llm.py` / `azure_vision_llm.py` | `llm_factory.py` |
| Embedding | `embedding/base_embedding.py` | `openai_embedding.py` / `azure_embedding.py` / `ollama_embedding.py` | `embedding_factory.py` |
| Splitter | `splitter/base_splitter.py` | `recursive_splitter.py` | `splitter_factory.py` |
| VectorStore | `vector_store/base_vector_store.py` | `chroma_store.py` | `vector_store_factory.py` |
| Reranker | `reranker/base_reranker.py` | `cross_encoder_reranker.py` / `llm_reranker.py` / `NoneReranker` | `reranker_factory.py` |
| Evaluator | `evaluator/base_evaluator.py` | `custom_evaluator.py`（+ `observability/evaluation/ragas_evaluator.py`） | `evaluator_factory.py` |

**配置文件**：`config/settings.yaml`（LLM / Embedding / Vision LLM / VectorStore / Retrieval / Rerank / Evaluation / Observability / Dashboard 九大块）

**自检问题**：
- 新增一个 LLM Provider 要改哪几个文件？（答：新增实现类 + 工厂注册 + settings.yaml，共 3 处）
- 工厂模式相比 `if provider == "openai"` 硬编码，优势在哪？

---

## ① 数据预处理（Loader / 解析）

**原理**：把异构原始文档解析成统一内部表示，**只做格式统一 + 结构抽取 + 引用收集，不负责切分**。

**项目的关键决策**：
1. **统一输出 canonical Markdown** —— 刻意选择，因为下游 `RecursiveCharacterTextSplitter` 依赖 Markdown 结构（标题/段落/代码块）才能切得好
2. **Loader 不切分** —— 职责分离，让切分策略可独立迭代与度量
3. **前置去重（Early Exit）** —— 解析前先算 SHA256，查 `ingestion_history`，命中且 `success` 则**跳过全部后续处理**（解析/切分/LLM 重写），实现零成本增量更新

**源码**：
| 文件 | 关键内容 |
|------|---------|
| `src/libs/loader/pdf_loader.py` | PDF → Markdown（MarkItDown），图片提取 |
| `src/libs/loader/base_loader.py` | Loader 抽象基类 |
| `src/libs/loader/file_integrity.py` | SHA256 指纹 + SQLite `ingestion_history` |
| `src/core/types.py` | `Document` / `Chunk` / `ChunkRecord` 契约定义 |
| `src/ingestion/chunking/document_chunker.py` | `split_document()` L75、`_generate_chunk_id()` L140 |

**技术栈**：MarkItDown（PDF 解析）、SQLite（`data/db/ingestion_history.db`）

**自检问题**：
- 为什么选 MarkItDown 而不是 PyPDF2 / pdfplumber？（答：直接产出 Markdown 形态，配合下游 splitter 的 separators）
- SHA256 去重和"按文件名去重"的本质区别？（答：文件名变但内容不变时应复用，内容变但文件名不变时必须重跑）

---

## ② 分割策略（Splitter / Chunking）

**原理**：把长文档切成语义完整、可独立检索的片段，并保留定位信息。

**项目采用两层分割**（这是精髓）：

| 层次 | 手段 | 位置 | 作用 |
|------|------|------|------|
| **粗切分** | LangChain `RecursiveCharacterTextSplitter` | `src/libs/splitter/recursive_splitter.py` | 按 Markdown separators 语义感知切分 |
| **精加工** | LLM 智能重组 | `src/ingestion/transform/chunk_refiner.py` | 合并被物理切断的段落、剔除页眉页脚噪点，产出**自包含（Self-contained）语义单元** |

**关键设计**：Splitter 只负责"切"，"重组去噪"刻意放在 ③ Transform 阶段——**职责分离**。

**Chunk 必带字段**：`source`、`chunk_index`、`start_offset/end_offset`、`image_refs`

**源码**：
- `src/libs/splitter/recursive_splitter.py`
- `src/ingestion/chunking/document_chunker.py` → `_inherit_metadata()` L171（元数据继承）
- `config/settings.yaml` → splitter 配置块（chunk_size / chunk_overlap / separators）

**自检问题**：
- chunk_size 和 chunk_overlap 分别影响什么？overlap 太大会怎样？（答：召回冗余 + 存储膨胀 + 重排干扰）
- 为什么"智能重组"不放在 Splitter 内部？（答：让切分策略保持纯粹可度量，LLM 增强可独立开关/重试）

---

## ③ 增强与向量化（Transform + Embedding）

这是**两个环节**，但耦合最紧，也是 ETL 管道的"智力"环节。

### 3a. Transform（三个增强器）

| 增强器 | 文件 | 作用 |
|--------|------|------|
| **ChunkRefiner** | `transform/chunk_refiner.py` | LLM 二次加工：合并相关段落、去噪。规则 `_rule_based_refine()` L275 + LLM `_llm_refine()` L346 |
| **MetadataEnricher** | `transform/metadata_enricher.py` | LLM 生成 `Title` / `Summary` / `Tags` 注入 metadata |
| **ImageCaptioner** | `transform/image_captioner.py` | Vision LLM 生成图片描述，**缝合进 Chunk 正文** |

**工程特性**：每个 Transform 原子化 + 幂等，**支持单 Chunk 独立重试**，避免 LLM 调用失败导致整篇文档中断。三者都有 `_transform_parallel` / `_transform_sequential` 双路径。

**Prompt 外置**：`config/prompts/chunk_refinement.txt`、`metadata_enrichment.txt`、`image_captioning.txt`

### 3b. 多模态：Image-to-Text（本项目重点选型）

**用户查询命中含图 Chunk 的完整链路**：
```
Loader     识别图片 → 生成 image_id → 正文插占位符 [IMAGE: {id}] → metadata.images[]
Splitter   切分时保留 image_refs，确保图与说明文字同 Chunk
Transform  Vision LLM 生成结构化描述 → 缝合进正文 [图片描述: ...]
Storage    双轨：向量库存"含描述的 Chunk"，文件系统存"原始图片"
查询命中    image_refs → 查 image_index.db → 读文件 → Base64 → ImageContent
```

**为什么不用 CLIP？**（对比必须能讲）
| 方案 | 优势 | 劣势 |
|------|------|------|
| **Image-to-Text**（本项目） | 架构统一、复用文本链路、检索阶段零额外成本 | 描述质量依赖 LLM，可能丢视觉细节 |
| Multi-Embedding (CLIP) | 保留原始视觉特征、支持图搜图 | 需额外向量库，架构复杂度高 |

**选型理由**：架构统一 + 语义对齐（描述与文本查询天然同空间）+ 成本可控（仅摄取时调一次）+ 渐进增强（未来可叠加 CLIP，无需重构）

**Vision LLM 双模型策略**：GPT-4o（国际化/Azure）/ Qwen-VL-Max（国内/中文）；描述注入**推荐正文**（能被 Embedding 覆盖，可直接检索）

**降级策略**：Vision LLM 不可用 → 保留占位符，标记 `has_unprocessed_images: true`，**不阻塞 Ingestion**

### 3c. Embedding（双路向量化）

| 路 | 用途 | 解决什么 |
|----|------|---------|
| **Dense** | 语义向量（OpenAI text-embedding-3 / BGE） | "词不同意同" |
| **Sparse** | BM25 稀疏向量 / SPLADE | 专有名词精确查找 |

**差量计算**：调昂贵 Embedding API 前先算 Chunk 内容哈希，只对不存在的新哈希向量化；文件名变但内容未变 → 复用已有向量。

**源码**：`src/ingestion/embedding/dense_encoder.py`、`sparse_encoder.py`、`batch_processor.py`（`batch_size` 驱动批处理）

**自检问题**：
- 为什么图转文的描述要注入正文而不是 metadata？（答：正文才能被 Embedding 覆盖，metadata 需额外索引配置）
- 双路编码为什么并行而不是串联？（答：无依赖关系，并行降延迟）

---

## ④ 存储索引（Upsert & Storage）

**原理**：把向量 + 原文 + 富元数据原子写入，并保证幂等。

**All-in-One 策略**（一条记录同时含两部分）：
1. **Index Data**：Dense Vector + Sparse Vector
2. **Payload Data**：完整 Chunk 原文 + 富 Metadata

**机制优势**：命中 ID 后**立即取回正文，无需额外查库（Lookup）**，保障检索毫秒级响应。

**幂等性核心公式**：
```
chunk_id = hash(source_path + section_path + content_hash)
```
采用 Upsert 语义 + Batch 事务写入 → 同一文档多次处理，库里永远只有一份最新副本。

**四种存储 + 跨存储协调删除**（`DocumentManager.delete_document()` L189）：
1. **Chroma** —— 按 `metadata.source` 删 chunk 向量
2. **BM25 Indexer** —— `remove_document()` 移除倒排条目
3. **ImageStorage** —— 删该文档关联图片文件
4. **FileIntegrity** —— 移除处理记录（使文件可重新摄入）

**源码**：
| 文件 | 关键函数 |
|------|---------|
| `src/ingestion/storage/vector_upserter.py` | 向量写入 |
| `src/ingestion/storage/bm25_indexer.py` | `build()` L100、`query()` L225、`remove_document()` L364、`_calculate_bm25_score()` L450 |
| `src/ingestion/storage/image_storage.py` | `save_image()` L138、`register_image()` L230 |
| `src/ingestion/document_manager.py` | `list_documents()` / `get_document_detail()` / `delete_document()` / `get_collection_stats()` |
| `src/libs/vector_store/chroma_store.py` | `delete_by_metadata()` |

**SQLite 三处落地**（Local-First，零外部数据库依赖）：
| 用途 | 文件 |
|------|------|
| 文件完整性 | `data/db/ingestion_history.db` |
| 图片索引映射 | `data/db/image_index.db` |
| BM25 索引元数据 | `data/db/bm25/`（当前 pickle） |

**自检问题**：
- 为什么要 `source_path + section_path + content_hash` 三者组合，而不是只用内容哈希？（答：同一段内容出现在不同文档/章节时不能互相覆盖）
- BM25 索引为什么单独存而不放进向量库？（答：BM25 是倒排索引 + IDF 统计，与向量库数据模型不同）

---

## ⑤ 查询理解与召回（Query Processing + Hybrid Search）

**原理**：先理解查询，再并行多路召回，最后融合成一个候选集。

### 5a. Query Processing（`query_processor.py`）

**核心假设（边界划得很清楚）**：输入 Query 已由上游 MCP Host 完成**指代消歧和上下文补全（De-referencing）**——本项目不处理多轮对话消歧。

- **Keyword Extraction**：提取关键实体与动词、去停用词 → 稀疏检索 Token 列表
- **Query Expansion**：同义词/别名/缩写扩展，**默认策略："扩展只融入稀疏路，稠密路保持单次"**
  - Sparse 路：关键词 + 同义词合并为 OR 表达式，**只查一次**，原始关键词可加权抑制语义漂移
  - Dense 路：用原始 query 生成 embedding，**只查一次**，不为每个同义词单独触发向量检索

**关键函数**：`process()` L117、`_extract_filters()` L168、`_tokenize()` L210、`_filter_keywords()` L239

### 5b. Hybrid Search（`hybrid_search.py`）

**并行双路召回**：
- **Dense 路**：Query Embedding → 向量库 Cosine 相似度 → Top-N
- **Sparse 路**：BM25 → 倒排索引 → Top-N

**RRF 融合**（`fusion.py` 的 `RRFFusion`）：
```
Score = 1/(k + Rank_Dense) + 1/(k + Rank_Sparse)
```
**关键洞察**：RRF **不依赖各路分数的绝对值，只看排名倒数**——因为 Dense 的 Cosine 分数和 BM25 的分数**根本不可比**，直接加权求和需要归一化且极不稳定。

**配置**：`top_k_dense: 20`、`top_k_sparse: 20` → 融合出 Top-M 候选

**关键函数**：
- `search()` L203（主入口）
- `_run_parallel_retrievals()` L421（并行召回）
- `_run_dense_retrieval()` L486 / `_run_sparse_retrieval()` L534
- `_fuse_results()` L582
- `fusion.py` → `fuse()` L84、`fuse_with_weights()` L181、`rrf_score()` L287

**自检问题**：
- RRF 的 `k` 参数起什么作用？调大会怎样？（答：平滑，k 越大排名差异影响越小）
- 为什么扩展只走稀疏路？（答：控制成本与复杂度，避免多次 Embedding 调用）
- 混合检索相对纯向量，在什么场景下收益最大？（答：专有名词/组件名/错误码等精确匹配）

---

## ⑥ 精排与过滤（Filtering + Rerank）

**原理**：在 Top-M 候选上做高精度排序，并施加结构化约束。

### 6a. Metadata Filtering 策略

**核心原则（务必记住这句）**：
> **先解析、能前置则前置、无法前置则后置兜底**

| 情况 | 处理 |
|------|------|
| 硬约束 + 索引支持 | 检索阶段 **Pre-filter**（缩小候选集，降成本） |
| 无法前置（字段缺失/质量不稳） | Rerank 前 **Post-filter** 作 safety net |
| 字段缺失 | **宽松包含（missing → include）**，避免误杀召回 |
| 软偏好（如"更近期更好"） | **不硬过滤**，作为排序信号在融合/重排阶段加权 |

**关键函数**：`hybrid_search.py` → `_merge_filters()` L335、`_apply_metadata_filters()` L677、`_matches_filters()` L704

### 6b. Rerank（可插拔精排）

| 后端 | 配置值 | 特点 |
|------|--------|------|
| **None** | `none` | 直接返回 RRF 排名，零成本 |
| **Cross-Encoder** | `cross_encoder` | `[Query, Chunk]` 对打分，CPU 下建议 M=10~30 |
| **LLM Rerank** | `llm` | 需更强指令理解，M≤20，要求严格 JSON 输出 |

**默认配置**：`backend: cross_encoder`、`model: cross-encoder/ms-marco-MiniLM-L-6-v2`、`top_m: 30`

**Graceful Fallback（必须能讲）**：精排超时 / 失败 / 不可用 → **回退到 RRF Top-K 排名**，保证系统可用性与结果稳定性。

**源码**：
- `src/libs/reranker/cross_encoder_reranker.py` ⚠️ **README 标注未测试**
- `src/libs/reranker/llm_reranker.py`（读 `config/prompts/rerank.txt`）
- `src/libs/reranker/base_reranker.py`（含 `NoneReranker`）
- `src/core/query_engine/reranker.py` → `rerank()` L235（Core 层编排 + fallback 逻辑）
- `config/settings.yaml` → `rerank.top_m` / `top_k_final`

**自检问题**：
- Cross-Encoder 和 Bi-Encoder（Dense 检索用的）本质区别？（答：Cross 是 query 和 doc 拼接后交互编码，精度高但无法预计算；Bi 可预计算向量，快但精度低）
- 为什么要"粗排→精排"两段式，不直接用 Cross-Encoder 全量打分？（答：Cross-Encoder 对每个候选都要跑一次模型，全量不可接受）
- Fallback 为什么回退到 RRF 而不是报错？（答：可用性优先，检索降级优于服务不可用）

---

## ⑦ 评测与可观测（Evaluation + Trace）

**这是最容易被忽略、但面试最加分的一条线。**

### 7a. 双链路 Trace（白盒化）

| 链路 | 覆盖阶段 |
|------|---------|
| **Ingestion Trace** | load → split → transform → embed → upsert |
| **Query Trace** | 预处理 → Dense/Sparse 召回 → 融合 → 重排 → 响应构建 |

**设计**：`TraceContext` 显式调用模式，低侵入记录各阶段**耗时、候选数量、分数分布** → 落成 **JSON Lines**（`logs/traces.jsonl`），**零外部依赖**（不需 LangSmith / LangFuse）。

**源码**：`src/core/trace/trace_context.py` → `record_stage()` L41、`finish()` L68、`elapsed_ms()` L75、`get_stage_data()` L118；`trace_collector.py` → `collect()` L35

### 7b. 评估体系

**可插拔**：`CompositeEvaluator` 支持多评估器并行执行与汇总。

**DEV_SPEC 明确的达标线**（4.3 节）：

| 类型 | 指标 | 目标 |
|------|------|------|
| 检索 | **Hit Rate@K** | ≥ 90% |
| 检索 | **MRR** | ≥ 0.8 |
| 检索 | **NDCG@K** | ≥ 0.85 |
| 生成 | **Faithfulness** | ≥ 0.9 |
| 生成 | **Answer Relevancy** | ≥ 0.85 |

**Golden Test Set 回归**：`tests/fixtures/golden_test_set.json`（"问题-答案-来源文档"三元组），拒绝"凭感觉调优"——每次改 Chunk Size / 换 Reranker 都有量化分数支撑。

**源码**：
- `src/observability/evaluation/eval_runner.py` → `EvalRunner` L141、`run()` L192、`_retrieve()` L311
- `src/observability/evaluation/ragas_evaluator.py` → `RagasEvaluator` L42、`_run_ragas()` L150
- `src/observability/evaluation/composite_evaluator.py` → `CompositeEvaluator` L23
- `src/libs/evaluator/custom_evaluator.py` ⚠️ **README 标注未测试**
- `scripts/evaluate.py`（离线评估入口）

**自检问题**：
- Hit Rate 和 MRR 的区别？（答：Hit Rate 只看有没有命中，MRR 看命中位置排名）
- 为什么需要 Golden Test Set 而不是每次随机测？（答：可回归、可对比、避免"感觉变好了"）

---

## 🔌 MCP 服务层（能力出口）

**原理**：把上面 7 条链路的最终能力，按 MCP 标准暴露成 Tools，供 Copilot / Claude Desktop 调用。

**技术细节**：JSON-RPC 2.0 + **Stdio Transport**（零配置、零网络依赖，天然适合私有知识库）

**暴露的 3 个 Tool**：
| Tool | 用途 |
|------|------|
| `query_knowledge_hub` | 核心检索问答 |
| `list_collections` | 列出知识集合 |
| `get_document_summary` | 获取文档摘要 |

**响应支持多模态**：`TextContent` + `ImageContent`（Base64），含结构化 Citation 引用。

**异步处理**：三个 Tool 都通过 `asyncio.to_thread()` 把阻塞调用移入线程池，避免阻塞 MCP 事件循环。

**源码**：
- `src/mcp_server/server.py`（入口 + `run_stdio_server_async()`）
- `src/mcp_server/protocol_handler.py` → `handle_list_tools()` L247、`handle_call_tool()` L253
- `src/mcp_server/tools/query_knowledge_hub.py` → `_perform_search()` L317、`_apply_rerank()` L352
- `src/mcp_server/tools/list_collections.py`、`get_document_summary.py`
- `src/core/response/` → `response_builder.py` / `multimodal_assembler.py` / `citation_generator.py`

---

## 研究推进顺序建议

| 顺序 | 内容 | 理由 |
|------|------|------|
| **1** | ⚙️ 可插拔架构 | 地基，不先看后面处处是黑盒 |
| **2** | ① + ② | 摄取域起点，理解 canonical Markdown 与两层分割 |
| **3** | ⑤ + ⑥ | **本项目最核心的技术含量**，面试必问 RRF 与两段式检索 |
| **4** | ③ | 多模态 Image-to-Text 是差异化亮点 |
| **5** | ④ | 幂等与跨存储协调，工程细节 |
| **6** | ⑦ | 评测与 Trace，补简历数字的唯一数据来源 |
| **7** | 🔌 MCP 层 | 收口，理解怎么被 Copilot 调用 |

**代码入口脚本**（跑通链路用）：
- `scripts/ingest.py` —— 走通 ①→④
- `scripts/query.py` —— 走通 ⑤→⑥
- `scripts/evaluate.py` —— 走通 ⑦
- `scripts/start_dashboard.py` —— 可视化查看 Trace 与评估

---

## ⚠️ 已知落差清单（研究时先验证）

| 模块 | 文档状态 | 实际状态 | 建议 |
|------|---------|---------|------|
| Cross-Encoder Reranker | 配置默认启用 | `README` 标注**未测试**，需下载本地模型 `cross-encoder/ms-marco-MiniLM-L-6-v2` | 先改 `settings.yaml` 用 `none` 跑通，再单独验证 |
| Custom Evaluator | 框架完成 | `README` 标注**未测试** | 需自备测试数据集 |
| 图片处理 | 设计完整 | 需确认 Vision LLM 是否已配置可用 | 无 Vision LLM 时应走降级路径 |

---

## 简历可用的量化线索（需自己实测填充）

以下指标在项目中有采集能力，但**当前没有实跑数据**，写简历前必须自己跑一遍：

- **检索质量**：Rerank 前后 Top-1 命中率变化、Hit Rate@K、MRR、NDCG
- **延迟**：Dense / Sparse 单路耗时、融合耗时、精排耗时、端到端 P50/P95
- **增量效率**：SHA256 跳过的文件占比、复用向量占比（体现 API 成本节省）
- **摄取规模**：处理文档数、生成 Chunk 数、图片数、Caption 覆盖率
- **检索对比**：纯 Dense vs 纯 BM25 vs Hybrid+RRF vs +Rerank（消融实验）

> 数据来源：`logs/traces.jsonl`（Trace 已记录各阶段耗时与候选数）+ `scripts/evaluate.py`（Golden Set 指标）
