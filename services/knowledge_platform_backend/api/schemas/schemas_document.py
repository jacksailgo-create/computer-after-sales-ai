# services/knowledge_platform_backend/api/schemas_document.py
from pydantic import BaseModel, Field
from typing import List, Optional, Generic, TypeVar

# 定义泛型变量，用于动态指定 data 的类型
T = TypeVar("T")

# ==========================================
# 🌟 全局通用响应基类
# ==========================================
class BaseResponse(BaseModel, Generic[T]):
    code: int = Field(default=200, description="业务状态码")
    message: str = Field(default="success", description="提示信息")
    data: Optional[T] = Field(default=None, description="业务数据")

# ==========================================
# 接口 1：上传落盘响应数据
# ==========================================
class UploadResponseData(BaseModel):
    id: int = Field(description="文档记录在数据库中的 ID")
    filename: str = Field(description="原始文件名")
    status: str = Field(description="当前状态 (例如: pending)")

# ==========================================
# 接口 2：文件列表项数据
# ==========================================
class DocumentItem(BaseModel):
    id: int
    fileName: str
    status: str
    message: str = Field(description="供前端展示的友好提示语")
    time: str = Field(description="创建时间 (yyyy-MM-dd HH:mm:ss)")

# ==========================================
# 接口 3：预览响应数据
# ==========================================
class PreviewResponseData(BaseModel):
    id: int
    content: Optional[str] = Field(description="解析后的 Markdown 内容")

# ==========================================
# 接口 4：更新内容请求体 (取代以前模糊的 payload: dict)
# ==========================================
class UpdateContentRequest(BaseModel):
    content: str = Field(..., description="人工清洗后的最新文本内容", min_length=1)