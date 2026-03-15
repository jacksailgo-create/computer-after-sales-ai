# from backend.rag.retriever import DenseRetrieverManager
from services.knowledge_platform_backend.rag.hybrid_search import HybridRetrieverManager

if __name__ == "__main__":
    # 创建向量检索器实例
    retriever = HybridRetrieverManager()

    # 测试向量检索
    query = "电脑经常死机怎么办？"
    docs = retriever.search(query)
    for doc in docs:
        print(doc.metadata)
        print(doc.page_content)
    # print(f"检索结果: {docs}")