import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

# 引入请求模型和服务
from customer_service_backend.api.schemas.request import ChatMessageRequest, UserSessionsRequest
from customer_service_backend.service.agent_service import MultiAgentService
from customer_service_backend.service.session_service import session_service

# 初始化日志 (假设 core.logger 已在 main.py 或 __init__.py 中完成了基础配置)
logger = logging.getLogger(__name__)

# 1. 定义请求路由器，统一抽取 /api 前缀，让代码更整洁
router = APIRouter(prefix="/api", tags=["Chat & Sessions (对话与会话管理)"])


# ==========================================
# 响应数据模型 (Response Schemas)
# 作用：让 FastAPI 自动生成完美的接口文档，并对返回数据进行严格的类型校验
# ==========================================
class SessionItemResponse(BaseModel):
    session_id: str = Field(description="会话唯一标识")
    create_time: str = Field(description="会话创建时间 (ISO 8601)")
    total_messages: int = Field(description="非系统消息的总条数")
    memory: list = Field(description="会话的历史消息记录")
    error: Optional[str] = Field(default=None, description="读取该会话时的异常信息")

class UserSessionsResponse(BaseModel):
    success: bool = Field(description="请求是否成功")
    user_id: str = Field(description="用户标识")
    total_sessions: int = Field(default=0, description="总会话数")
    sessions: List[SessionItemResponse] = Field(default_factory=list, description="会话列表")
    error: Optional[str] = Field(default=None, description="全局错误信息")


# ==========================================
# API 路由实现
# ==========================================

@router.post("/query", summary="智能体流式对话接口", response_class=StreamingResponse)
async def query(request: ChatMessageRequest) -> StreamingResponse:
    """
    接收用户提问并返回 SSE (Server-Sent Events) 流式响应。
    """
    user_id = request.context.user_id
    session_id = request.context.session_id
    user_query = request.query
    flag = request.flag

    # 截取查询内容的前20个字符用于日志打印，防止日志刷屏
    safe_query_log = user_query if len(user_query) < 20 else f"{user_query[:20]}..."
    logger.info(f"[Query] 开始处理任务 | 用户: {user_id} | 会话: {session_id} | 提问: {safe_query_log} | Flag: {flag}")

    try:
        # 调用 AgentService 获取异步生成器 (Async Generator)
        async_generator_result = MultiAgentService.process_task(request, flag=flag)

        # 封装为 StreamingResponse 并加上标准的 SSE 响应头
        return StreamingResponse(
            content=async_generator_result,
            status_code=200,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",   # 禁用浏览器及中间代理缓存
                "Connection": "keep-alive",    # 保持长连接
                "X-Accel-Buffering": "no",     # 禁用 Nginx 缓冲，确保流式输出即时到达
            }
        )
    except Exception as e:
        # 注意：这里的 try-except 只能捕获 generator 创建前的同步错误。
        # 真正的流传输错误已在 MultiAgentService 的 ResponseFactory 中被捕获并推送到前端。
        logger.error(f"[Query] 核心服务初始化异常 | 用户: {user_id} | 错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"内部智能体服务异常: {str(e)}")


@router.post("/user_sessions", summary="获取用户历史会话列表", response_model=UserSessionsResponse)
def get_user_sessions(request: UserSessionsRequest):
    """
    获取指定用户的所有会话记忆数据，按时间倒序排列。
    """
    user_id = request.user_id
    logger.info(f"[UserSessions] 收到检索请求 | 用户: {user_id}")

    try:
        # 调用底层存储检索历史会话
        all_sessions = session_service.get_all_sessions_memory(user_id)
        logger.info(f"[UserSessions] 检索成功 | 用户: {user_id} | 共获取 {len(all_sessions)} 个会话")

        # 此时 FastAPI 会根据 response_model 自动校验并转换返回格式
        return UserSessionsResponse(
            success=True,
            user_id=user_id,
            total_sessions=len(all_sessions),
            sessions=all_sessions
        )

    except Exception as e:
        # 异常降级处理：即使失败也返回 200 OK，但包含 error 字段供前端弹窗提示
        logger.error(f"[UserSessions] 检索失败 | 用户: {user_id} | 错误: {str(e)}", exc_info=True)
        return UserSessionsResponse(
            success=False,
            user_id=user_id,
            error=str(e)
        )