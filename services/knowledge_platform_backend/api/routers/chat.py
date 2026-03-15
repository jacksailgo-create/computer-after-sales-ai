# services/knowledge_platform_backend/api/chat.py

import logging
from fastapi import APIRouter, HTTPException
from ..schemas.schemas_chat import ChatRequest, ChatCompletionResponse, ChatCompletionData
from knowledge_platform_backend.services.knowledge_service import knowledge_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/chat",
    tags=["AI Chat & Retrieval"]
)

@router.post("/completions",
             summary="多路检索与大模型对话",
             response_model=ChatCompletionResponse)
async def chat_with_rag(request: ChatRequest):
    """
    接收提问，交由 KnowledgeService 执行【检索+生成】流程。
    """
    query = request.query
    if not query.strip():
        raise HTTPException(status_code=400, detail="提问不能为空")

    try:
        logger.info(f"🗣️ [KB-Chat] 收到检索生成请求: '{query}'")

        # 调用底层 Service 层 (封装了检索、Prompt 拼接、LLM 生成)
        # 假设返回结构为 {"answer": "...", "sources": [...], "chunks": [...]}
        result = await knowledge_service.generate_rag_response(query)

        # 🌟 按照 Schema 结构进行封装
        # 即使底层 result 包含多余字段，此处也会被 Schema 过滤，保证接口纯净
        return ChatCompletionResponse(
            code=200,
            message="success",
            data=ChatCompletionData(
                answer=result.get("answer", ""),
                sources=list(set(result.get("sources", []))), # 自动去重
                # raw_chunks=result.get("chunks", [])
            )
        )

    except Exception as e:
        logger.exception(f"❌ [KB-Chat Error] 链路异常: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"知识库决策引擎异常: {str(e)}"
        )