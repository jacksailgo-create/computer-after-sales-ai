from enum import Enum
from typing import Optional, Union, Literal
from pydantic import BaseModel, Field


# ==========================================
# 1. 枚举类型定义 (Enums)
# ==========================================

class ContentKind(str, Enum):
    """
    内容语义分类：前端根据此字段决定消息渲染在哪个 UI 区域。
    """
    THINKING = 'THINKING'  # 思考/推理过程 -> 渲染在可折叠的灰色区域
    PROCESS = 'PROCESS'  # 系统级流程提示（如"正在调用搜索工具"） -> 渲染在折叠区域
    ANSWER = 'ANSWER'  # 最终正式回答 -> 渲染在主聊天气泡中


class StreamStatus(str, Enum):
    """
    SSE 数据流的生命周期状态。
    """
    IN_PROGRESS = 'IN_PROGRESS'  # 流正在持续传输中
    FINISHED = 'FINISHED'  # 流传输正式结束


class StopReason(str, Enum):
    """
    流生成结束的具体原因，仅在 status 为 FINISHED 时具有实际意义。
    """
    NORMAL = 'NORMAL'  # 大模型自然输出完毕
    MAX_TOKENS = 'MAX_TOKENS'  # 触碰到了设定的最大 Token 限制而截断
    ERROR = 'ERROR'  # 执行过程中发生异常（如网络中断、工具调用失败）


# ==========================================
# 2. 消息体基类与派生类 (Polymorphic Message Bodies)
# ==========================================

class MessageBody(BaseModel):
    """
    消息体基类。
    """
    contentType: str = Field(description="区分不同消息类型的唯一标识符")


class TextMessageBody(MessageBody):
    """
    文本消息体：在流式传输过程中，承载每一个字的具体内容。
    """
    # 使用 Literal 强制限定类型，这是 Pydantic 解析 Union 多态的核心机制
    contentType: Literal['sagegpt/text'] = 'sagegpt/text'
    text: str = Field(default='', description="增量的文本切片内容 (Chunk)")
    kind: ContentKind = Field(..., description="文本的分类属性（思考/流程/回答）")


class FinishMessageBody(MessageBody):
    """
    结束信号体：不携带文本内容，仅作为服务端发出的“流结束”硬标志。
    """
    contentType: Literal['sagegpt/finish'] = 'sagegpt/finish'


# ==========================================
# 3. 顶层 SSE 数据包封装 (The SSE Packet)
# ==========================================

class PacketMeta(BaseModel):
    """
    数据包的元数据附加信息。
    """
    createTime: str = Field(description="当前数据包生成的 ISO 8601 时间戳")
    finishReason: Optional[StopReason] = Field(default=None, description="触发结束的原因")
    errorMessage: Optional[str] = Field(default=None, description="若发生错误，此处携带详细的错误日志文本")


class StreamPacket(BaseModel):
    """
    SSE 流数据包 (原 MessageResponse)。
    这是后端通过 yield 发送给前端的「最小标准数据单元」。
    对应前端收到的 `data: {...}` 中的 JSON 对象。
    """
    id: str = Field(description="该轮对话或该数据包的唯一 ID (如 msg_12345)")

    # 核心设计：Union 允许该字段既可以是具体的文本块，也可以是纯粹的结束信号
    content: Union[TextMessageBody, FinishMessageBody] = Field(description="实际的消息承载体")

    status: StreamStatus = Field(description="当前流的总体状态")
    metadata: PacketMeta = Field(description="数据包的元信息")