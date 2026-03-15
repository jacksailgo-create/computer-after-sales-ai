import logging
from typing import List
from fastapi import APIRouter, HTTPException, Depends

# 1. 引入刚才封装好的标准响应模型
from knowledge_platform_backend.api.schemas.schemas_kb import (
    SearchRequest,
    SearchResponse,
    SearchResponseData,
    DocumentResult,
)

# 2. 引入底层向量库管理器
from knowledge_platform_backend.rag.vector_store import VectorStoreManager

# 3. 获取配置好的日志记录器
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/kb",
    tags=["Knowledge Base Retrieval"]
)

# ==========================================
# 依赖注入：获取向量库实例
# ==========================================
def get_vector_store():
    """
    每次请求时获取向量库连接。
    VectorStoreManager 内部会调用 ModelFactory 获取 Embedding。
    """
    try:
        manager = VectorStoreManager()
        # 假设 get_store() 返回的是 LangChain 的 VectorStore 对象 (如 Chroma)
        return manager.get_store()
    except Exception as e:
        logger.error(f"❌ 向量库加载失败: {e}")
        raise HTTPException(status_code=500, detail="向量数据库连接异常")


# ==========================================
# 接口 1：统计信息
# ==========================================
@router.get("/stats", summary="获取知识库存储状态")
async def get_kb_stats(db=Depends(get_vector_store)):
    """
    返回当前知识库中已向量化的文本块总数。
    """
    try:
        # ChromaDB 原生支持 count()
        count = db._collection.count()
        return {
            "code": 200,
            "message": "success",
            "data": {"total_chunks": count}
        }
    except Exception as e:
        logger.error(f"统计知识库失败: {e}")
        raise HTTPException(status_code=500, detail="无法获取统计数据")


# ==========================================
# 接口 2：语义检索 (核心对接接口)
# ==========================================
@router.post("/search", response_model=SearchResponse, summary="执行 RAG 语义检索")
async def search_knowledge_base(
    req: SearchRequest,
    db=Depends(get_vector_store)
):
    """
    接收用户 Query，返回最相关的知识片段及其元数据。
    """
    logger.info(f"🔍 [KB Search] 收到检索请求: '{req.query}' (top_k={req.top_k})")

    try:
        # 1. 调用向量库进行相似度搜索
        # similarity_search_with_score 会返回 List[Tuple[Document, float]]
        results = db.similarity_search_with_score(
            query=req.query,
            k=req.top_k,
            filter=req.filter
        )

        # 2. 数据模型转换：将 LangChain 对象转换为我们的 DocumentResult DTO
        formatted_results = []
        for doc, score in results:
            formatted_results.append(
                DocumentResult(
                    content=doc.page_content,
                    metadata=doc.metadata,
                    score=round(float(score), 4)  # 确保分数是标准浮点数并取 4 位小数
                )
            )

        # 3. 构建并返回标准化的响应体
        return SearchResponse(
            code=200,
            message="检索成功",
            data=SearchResponseData(
                total_found=len(formatted_results),
                results=formatted_results
            )
        )

    except Exception as e:
        # 使用 logger.exception 会自动捕获堆栈轨迹，方便排查 Embedding 报错或网络超时
        logger.exception(f"❌ [KB Search Error] 检索链条崩溃: {req.query}")
        raise HTTPException(
            status_code=500,
            detail=f"检索服务暂时不可用: {str(e)}"
        )