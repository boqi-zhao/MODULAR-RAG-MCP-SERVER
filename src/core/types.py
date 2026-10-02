"""贯穿整个流水线的核心数据类型与契约。

本模块定义了所有流水线阶段共用的基础数据结构：
- ingestion（加载、变换、嵌入、存储）
- retrieval（查询引擎、检索、重排）
- mcp_server（工具、响应格式化）

设计原则：
- 契约集中：所有阶段共用这些类型，避免相互耦合
- 可序列化：所有类型都支持 dict/JSON 互转
- 元数据可扩展：仅要求最少必需字段，支持灵活扩展
- 类型安全：完整的类型注解，便于静态分析
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional


@dataclass
class Document:
    """表示从数据源加载的原始文档。
    
    这是 Loader（如 PDF Loader）在切分前的输出。
    
    属性：
        id: 文档的唯一标识（如文件哈希或基于路径的 ID）
        text: 规范化 Markdown 格式的文档内容。
              图片以占位符表示：[IMAGE: {image_id}]
        metadata: 文档级元数据，包括：
            - source_path（必需）：原始文件路径
            - doc_type: 文档类型（如 'pdf'、'markdown'）
            - title: 提取或推断出的文档标题
            - page_count: 总页数（如适用）
            - images: 图片引用列表（见下方“图片字段规范”）
            - 以及任意其他自定义元数据
    
    图片字段规范（metadata.images）：
        结构：List[{"id": str, "path": str, "page": int, "text_offset": int, 
                  "text_length": int, "position": dict}]
        字段说明：
            - id: 图片唯一标识（格式：{doc_hash}_{page}_{seq}）
            - path: 图片文件存储路径（约定：data/images/{collection}/{image_id}.png）
            - page: 在原文档中的页码（可选，适用于 PDF 等分页文档）
            - text_offset: 占位符在 Document.text 中的起始字符位置（从 0 开始）
            - text_length: 占位符字符串长度（通常为 len("[IMAGE: {image_id}]")）
            - position: 图片在原文档中的物理位置信息（可选，如 PDF 坐标、像素位置）
        说明：text_offset 与 text_length 可精确定位占位符，
              支持同一图片多次出现的场景
    
    示例：
        >>> doc = Document(
        ...     id="doc_abc123",
        ...     text="# Title\\n\\nContent...",
        ...     metadata={
        ...         "source_path": "data/documents/report.pdf",
        ...         "doc_type": "pdf",
        ...         "title": "Annual Report 2025"
        ...     }
        ... )
    """
    
    id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """校验必需的元数据字段。"""
        if "source_path" not in self.metadata:
            raise ValueError("Document metadata must contain 'source_path'")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典以便序列化。"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """从字典创建 Document。"""
        return cls(**data)


@dataclass
class Chunk:
    """表示 Document 切分后的文本块。
    
    这是 Splitter 的输出、Transform 流水线的输入。
    每个 chunk 都保持对其源文档的可追溯性。
    
    属性：
        id: chunk 唯一标识（如基于哈希或顺序生成）
        text: chunk 内容（原文档文本的子集）。
              图片以占位符表示：[IMAGE: {image_id}]
        metadata: 从 Document 继承并扩展的 chunk 级元数据：
            - source_path（必需）：原始文件路径
            - chunk_index: 在文档中的顺序位置（从 0 开始）
            - start_offset: 在原文档中的字符偏移（可选）
            - end_offset: 在原文档中的字符偏移（可选）
            - source_ref: 指向父文档 ID 的引用（可选）
            - images: 落在本 chunk 范围内的 Document.images 子集（可选）
            - 从 Document 透传的任意文档级元数据
        start_offset: 在原文档中的起始字符位置（可选）
        end_offset: 在原文档中的结束字符位置（可选）
        source_ref: 指向父 Document.id 的引用（可选）
    
    说明：若 chunk 包含图片占位符，metadata.images 应只包含
          与本 chunk 文本范围相关的图片引用。
    
    示例：
        >>> chunk = Chunk(
        ...     id="chunk_abc123_001",
        ...     text="## Section 1\\n\\nFirst paragraph...",
        ...     metadata={
        ...         "source_path": "data/documents/report.pdf",
        ...         "chunk_index": 0,
        ...         "page": 1
        ...     },
        ...     start_offset=0,
        ...     end_offset=150
        ... )
    """
    
    id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None
    source_ref: Optional[str] = None
    
    def __post_init__(self):
        """校验必需的元数据字段。"""
        if "source_path" not in self.metadata:
            raise ValueError("Chunk metadata must contain 'source_path'")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典以便序列化。"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Chunk":
        """从字典创建 Chunk。"""
        return cls(**data)


@dataclass
class ChunkRecord:
    """表示已完成处理、可存储与检索的 chunk。
    
    这是嵌入流水线的输出，也是存入向量数据库的数据结构，
    在 Chunk 基础上增加了向量表示。
    
    属性：
        id: chunk 唯一标识（必须稳定，以保证幂等 upsert）
        text: chunk 内容（同 Chunk.text）。
              图片以占位符表示：[IMAGE: {image_id}]
        metadata: 扩展后的元数据，包括：
            - source_path（必需）：原始文件路径
            - chunk_index: 顺序位置
            - Chunk 中的全部元数据
            - images: 来自 Chunk 的图片引用（见 Document.images 规范）
            - Transform 流水线添加的增强信息（title、summary、tags）
            - image_captions: 应用多模态增强时为 Dict[image_id, caption_text]
        dense_vector: 稠密嵌入向量（如来自 OpenAI、BGE）
        sparse_vector: 用于 BM25/关键词匹配的稀疏向量（可选）
    
    说明：ImageCaptioner 生成的图片描述存放在 metadata.image_captions 中，
          是以 image_id 到生成描述文本的字典映射。
    
    示例：
        >>> record = ChunkRecord(
        ...     id="chunk_abc123_001",
        ...     text="## Section 1\\n\\nFirst paragraph...",
        ...     metadata={
        ...         "source_path": "data/documents/report.pdf",
        ...         "chunk_index": 0,
        ...         "title": "Introduction",
        ...         "summary": "Overview of project goals"
        ...     },
        ...     dense_vector=[0.1, 0.2, ..., 0.3],
        ...     sparse_vector={"word1": 0.5, "word2": 0.3}
        ... )
    """
    
    id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    dense_vector: Optional[List[float]] = None
    sparse_vector: Optional[Dict[str, float]] = None
    
    def __post_init__(self):
        """校验必需的元数据字段。"""
        if "source_path" not in self.metadata:
            raise ValueError("ChunkRecord metadata must contain 'source_path'")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典以便序列化。"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChunkRecord":
        """从字典创建 ChunkRecord。"""
        return cls(**data)
    
    @classmethod
    def from_chunk(cls, chunk: Chunk, dense_vector: Optional[List[float]] = None,
                   sparse_vector: Optional[Dict[str, float]] = None) -> "ChunkRecord":
        """由 Chunk 和向量创建 ChunkRecord。
        
        参数：
            chunk: 源 Chunk 对象
            dense_vector: 稠密嵌入向量
            sparse_vector: 稀疏向量表示
            
        返回：
            由 chunk 填充全部字段的 ChunkRecord
        """
        return cls(
            id=chunk.id,
            text=chunk.text,
            metadata=chunk.metadata.copy(),
            dense_vector=dense_vector,
            sparse_vector=sparse_vector
        )


# 便捷类型别名
Metadata = Dict[str, Any]
Vector = List[float]
SparseVector = Dict[str, float]


@dataclass
class ProcessedQuery:
    """表示处理完成、可用于检索的查询。
    
    这是 QueryProcessor 的输出，包含提取的关键词
    以及供下游 Dense/Sparse 检索器使用的解析后过滤器。
    
    属性：
        original_query: 用户原始查询字符串
        keywords: 去除停用词后提取的关键词列表
        filters: 过滤条件字典（如 {"collection": "api-docs"}）
        expanded_terms: 可选的同义词/扩展词列表（预留）
    
    示例：
        >>> pq = ProcessedQuery(
        ...     original_query="如何配置 Azure OpenAI？",
        ...     keywords=["配置", "Azure", "OpenAI"],
        ...     filters={"collection": "docs"}
        ... )
    """
    
    original_query: str
    keywords: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    expanded_terms: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典以便序列化。"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProcessedQuery":
        """从字典创建 ProcessedQuery。"""
        return cls(**data)


@dataclass
class RetrievalResult:
    """表示来自 Dense/Sparse 检索器的单条检索结果。
    
    这是 DenseRetriever、SparseRetriever 和 HybridSearch 的输出，
    为所有检索方法提供统一的检索结果契约。
    
    属性：
        chunk_id: 被检索 chunk 的唯一标识
        score: 相关性得分（越高越相关，归一化到 [0, 1]）
        text: 被检索 chunk 的实际文本内容
        metadata: 关联元数据（source_path、chunk_index、title 等）
    
    示例：
        >>> result = RetrievalResult(
        ...     chunk_id="doc1_chunk_003",
        ...     score=0.85,
        ...     text="Azure OpenAI 配置步骤如下...",
        ...     metadata={
        ...         "source_path": "docs/azure-guide.pdf",
        ...         "chunk_index": 3,
        ...         "title": "Azure Configuration"
        ...     }
        ... )
    """
    
    chunk_id: str
    score: float
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后校验字段。"""
        if not self.chunk_id:
            raise ValueError("chunk_id cannot be empty")
        if not isinstance(self.score, (int, float)):
            raise ValueError(f"score must be numeric, got {type(self.score).__name__}")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典以便序列化。"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RetrievalResult":
        """从字典创建 RetrievalResult。"""
        return cls(**data)
