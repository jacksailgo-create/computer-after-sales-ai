import logging
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

import core.logger
logger = logging.getLogger(__name__)


class MarkdownSmartSplitter:
    """
    Markdown 智能文本切分器。
    采用“标题层级 + 递归字符”双重策略，最大程度保留售后文档的上下文语义。
    """

    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 100):
        """
        初始化切分器
        :param chunk_size: 单个文本块的最大长度（字符数）。建议 300-800 之间。
        :param chunk_overlap: 相邻文本块的重叠字符数，防止关键信息在边界处被切断。
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 1. 定义需要提取的 Markdown 标题层级
        self.headers_to_split_on = [
            ("#", "Header 1"),  # 通常是文章大标题或故障名称
            ("##", "Header 2"),  # 通常是具体的排障步骤或原因分析
            ("###", "Header 3"),  # 更细分的细节
        ]

        # 初始化标题切分器
        self.markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on,
            strip_headers=False  # 设为 False，保留正文中的 # 符号，有助于 LLM 理解格式
        )

        # 2. 初始化递归字符切分器 (作为兜底机制)
        # 按照 段落(\n\n) -> 单行(\n) -> 空格( ) -> 字符 的优先级依次尝试切分
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", "。", "！", "？", " ", ""]
        )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        执行双重智能切分
        :param documents: 原始加载的 Document 列表 (带有全局 metadata)
        :return: 切分后的小块 Document 列表
        """
        if not documents:
            logger.warning("传入的文档列表为空，跳过切分。")
            return []

        logger.info(f"🔪 开始智能切分 {len(documents)} 篇长文档...")

        final_chunks = []

        for doc in documents:
            # 拿到我们在上一环节提取出来的全局元数据 (url, source 等)
            base_metadata = doc.metadata

            # 阶段一：按标题层级切分 (将长文本切成了多个带有标题属性的中等块)
            # 注意：MarkdownHeaderTextSplitter 接收的是纯字符串
            header_splits = self.markdown_splitter.split_text(doc.page_content)

            # 将原始的全局 metadata 缝合到这些切分出来的块中
            for split in header_splits:
                # split.metadata 此时包含了 {"Header 1": "xxx", "Header 2": "yyy"}
                # 我们把它和 base_metadata 合并
                merged_metadata = {**base_metadata, **split.metadata}
                split.metadata = merged_metadata

            # 阶段二：递归字符兜底切分 (防止某个标题下的内容超过了 chunk_size)
            # 这一步会自动继承上一步合并好的 merged_metadata
            recursive_splits = self.recursive_splitter.split_documents(header_splits)

            final_chunks.extend(recursive_splits)

        logger.info(f"✅ 切分完成！{len(documents)} 篇文档被切分成了 {len(final_chunks)} 个向量块。")
        return final_chunks