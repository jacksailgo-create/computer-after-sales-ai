from pydantic import BaseModel, Field
from typing import List, Optional

# ==========================================
# 1. 内部引用的子模型
# ==========================================
class SourceMetadata(BaseModel):
    """参考来源的元数据"""
    file_name: str = Field(..., alias="source") # 兼容 Chroma 的 source 字段
    content: str = Field(..., description="片段摘要")

class ChatRequest(BaseModel):
    query: str
    session_id: str = "default_session"

# ==========================================
# 2. 响应实体
# ==========================================
class ChatCompletionData(BaseModel):
    """RAG 生成结果的数据体"""
    answer: str = Field(..., description="大模型生成的最终答案")
    sources: List[str] = Field(default_factory=list, description="去重后的参考文档列表")
    # raw_chunks: List[SourceMetadata] = Field(default_factory=list, description="原始检索到的文本块，供溯源")

class ChatCompletionResponse(BaseModel):
    """顶级响应规范"""
    code: int = 200
    message: str = "success"
    data: ChatCompletionData