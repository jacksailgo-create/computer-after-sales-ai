import uuid
from datetime import datetime, timezone
from typing import Optional

# 确保这里的路径与你的实际项目结构一致
from customer_service_backend.api.schemas.response import (
    StreamPacket,
    TextMessageBody,
    FinishMessageBody,
    StreamStatus,
    PacketMeta,
    ContentKind,
    StopReason  # 👈 引入停止原因枚举
)


class ResponseFactory:
    """
    SSE 响应构建工厂：负责将纯文本和状态组装为符合严格 Pydantic 规范的数据包。
    """

    @staticmethod
    def _get_iso_time() -> str:
        """获取标准 ISO 8601 UTC 时间戳，前端解析最安全"""
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def build_text(
            text: str,
            kind: ContentKind,
            message_id: str  # 👈 强制要求传入 message_id，保证流传输期间 ID 唯一
    ) -> StreamPacket:
        """
        构建文本/推理片段响应 (流传输中)

        :param text: 文本切片 (Chunk)
        :param kind: 内容类型 (THINKING / PROCESS / ANSWER)
        :param message_id: 这轮 AI 回复的全局唯一标识
        """
        body = TextMessageBody(text=text, kind=kind)

        return StreamPacket(
            id=message_id,
            content=body,
            status=StreamStatus.IN_PROGRESS,
            metadata=PacketMeta(createTime=ResponseFactory._get_iso_time())
        )

    @staticmethod
    def build_finish(
            message_id: str,
            reason: StopReason = StopReason.NORMAL
    ) -> StreamPacket:
        """
        构建正常结束信号响应

        :param message_id: 这轮 AI 回复的全局唯一标识
        :param reason: 结束原因，默认为 NORMAL (正常输出完毕)
        """
        return StreamPacket(
            id=message_id,
            content=FinishMessageBody(),
            status=StreamStatus.FINISHED,
            metadata=PacketMeta(
                createTime=ResponseFactory._get_iso_time(),
                finishReason=reason
            )
        )

    @staticmethod
    def build_error(
            error_message: str,
            message_id: Optional[str] = None
    ) -> StreamPacket:
        """
        构建异常中断信号响应 (护栏机制)
        通知前端立刻停止 Loading 动画，并展示错误提示。
        """
        # 如果报错时连 message_id 都还没来得及生成，则临时分配一个
        if message_id is None:
            message_id = f"err_{uuid.uuid4().hex[:8]}"

        return StreamPacket(
            id=message_id,
            content=FinishMessageBody(),  # 错误包本身也是一个结束信号
            status=StreamStatus.FINISHED,
            metadata=PacketMeta(
                createTime=ResponseFactory._get_iso_time(),
                finishReason=StopReason.ERROR,
                errorMessage=error_message
            )
        )