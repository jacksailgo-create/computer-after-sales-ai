import logging
from typing import List
from langchain_core.documents import Document

# 🌟 直接引入你之前写好的 Chroma 向量库单例
from knowledge_platform_backend.rag.vector_store import vector_db

import core.logger
logger = logging.getLogger(__name__)

class DenseRetrieverManager:
    """
    纯向量检索器 (Dense Retriever)
    负责将用户的自然语言提问转化为向量，并在 ChromaDB 中搜索最相似的知识切片。
    """
    def __init__(self):
        logger.info("⚙️ 正在初始化向量检索器...")
        # 调用 LangChain 内置的 as_retriever 方法，将其转化为标准检索器
        # search_type="similarity": 使用余弦相似度
        # k=5: 每次召回最相关的 5 个文本块
        self.retriever = vector_db.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )
        logger.info("✅ 向量检索器初始化完成！")

    def search(self, query: str) -> List[Document]:
        """执行向量检索"""
        logger.info(f"🔍 收到检索请求: {query}")
        try:
            # invoke 会自动将 query 进行 Embedding，然后去 Chroma 匹配
            docs = self.retriever.invoke(query)
            logger.info(f"🎯 成功召回 {len(docs)} 个高价值知识切片")
            return docs
        except Exception as e:
            logger.error(f"❌ 向量检索发生异常: {e}")
            return []

# 实例化导出，供 API 路由直接使用
dense_retriever = DenseRetrieverManager()