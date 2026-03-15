import logging
import re
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

import core.logger
logger = logging.getLogger(__name__)


class QADocumentSplitter:
    """
    专为 QA (问答) 和标准化知识库设计的智能切分器。
    放弃破坏结构的 Header 切分，改为提取主标题并注入到每个子块中。
    """

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        # 售后文档的步骤往往连贯性强，适当调大 chunk_size，尽量把一整个 QA 塞进一个块里
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 仅按段落和句子切分，绝不按 # 标题切断问答连贯性
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", "。", "！", "？", " ", ""]
        )

    def _extract_main_title(self, text: str) -> str:
        """
        使用正则提取文档的核心大标题 (通常是第一个 # 或 ## 后面的内容)
        例如提取出："如何使用U盘安装Windows 7操作系统"
        """
        match = re.search(r'^(?:#|##)\s+(.*?)$', text, re.MULTILINE)
        if match:
            # 过滤掉像 "知识库 1", "问题描述", "解决方案" 这种无效标题
            title = match.group(1).strip()
            if title not in ["问题描述", "分类", "元数据", "解决方案"] and not title.startswith("知识库"):
                return title

            # 如果匹配到了无效标题，尝试往下再找一个
            matches = re.findall(r'^(?:#|##)\s+(.*?)$', text, re.MULTILINE)
            for t in matches:
                t = t.strip()
                if t not in ["问题描述", "分类", "元数据", "解决方案"] and not t.startswith("知识库"):
                    return t
        return "未知售后问题"

    def split_documents(self, documents: List[Document]) -> List[Document]:
        if not documents:
            return []

        logger.info(f"🔪 开始对 {len(documents)} 篇 QA 文档进行文脉连贯切分...")
        final_chunks = []

        for doc in documents:
            base_metadata = doc.metadata or {}
            content = doc.page_content

            # 1. 提取这篇文章的真正灵魂（比如：如何使用U盘安装Windows 7操作系统）
            main_title = self._extract_main_title(content)

            # 2. 如果整篇文章长度本来就不长（比如小于 800 字），直接不切！完整保留问答结构！
            if len(content) <= self.chunk_size:
                # 将主标题注入到元数据中，提高检索成功率
                doc.metadata = {**base_metadata, "main_title": main_title}
                # 为了让向量检索更准，我们可以在内容前面强制加上标题
                doc.page_content = f"【主题：{main_title}】\n{content}"
                final_chunks.append(doc)
                continue

            # 3. 如果文章过长必须切分，则使用兜底切分，并将大标题强制注入到每一块的开头！
            recursive_splits = self.recursive_splitter.split_text(content)

            for split_text in recursive_splits:
                new_doc = Document(
                    # 强行把大标题和切分后的段落绑死，防止该段落丢失上下文
                    page_content=f"【主题：{main_title}】\n{split_text}",
                    metadata={**base_metadata, "main_title": main_title}
                )
                final_chunks.append(new_doc)

        logger.info(f"✅ QA 文档切分完成，共产出 {len(final_chunks)} 个带强上下文的知识块。")
        return final_chunks