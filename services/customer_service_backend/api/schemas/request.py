from typing import Optional
from pydantic import BaseModel, Field

class UserContext(BaseModel):
    """
    用户上下文信息：用于标识请求来源，维护多轮对话状态。
    """
    user_id: str = Field(
        ...,
        description="当前用户的唯一标识 (如 UUID 或账号名)",
        example="root1"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="会话ID。传 None 表示新建会话，传已有 ID 表示继续该会话",
        example="session_1710483920"
    )


class ChatMessageRequest(BaseModel):
    """
    前端发起对话请求的入参结构。
    """
    query: str = Field(
        ...,
        description="用户输入的查询文本/指令",
        example="我的电脑蓝屏了，错误代码是 WHEA_UNCORRECTABLE_ERROR，怎么办？"
    )
    context: UserContext = Field(
        ...,
        description="包含用户和会话标识的上下文对象"
    )
    flag: bool = Field(
        default=True,
        description="预留的控制标志位（如：是否开启联网搜索/强制刷新缓存等）"
    )


class UserSessionsRequest(BaseModel):
    """
    获取用户历史会话列表的入参结构。
    """
    user_id: str = Field(
        ...,
        description="需要查询历史会话的用户唯一标识符",
        example="root1"
    )