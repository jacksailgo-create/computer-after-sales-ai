from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# ==========================================
# 1. 基础原子模型
# ==========================================

class DocumentResult(BaseModel):
    """单条检索结果实体"""
    content: str = Field(..., description="检索到的知识片段文本内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="文档元数据（如 source, page, doc_id 等）")
    score: float = Field(..., description="相似度检索分数 (通常分数越小越相似，或取决于算法)")

# ==========================================
# 2. 请求实体 (Request)
# ==========================================

class SearchRequest(BaseModel):
    """检索请求体"""
    query: str = Field(..., min_length=1, description="用户的自然语言提问")
    top_k: int = Field(default=4, ge=1, le=20, description="返回最相关的片段数量")
    filter: Optional[Dict[str, Any]] = Field(None, description="元数据过滤条件 (例如 {'source': 'manual.pdf'})")

# ==========================================
# 3. 响应实体 (Response)
# ==========================================

class SearchResponseData(BaseModel):
    """搜索结果的聚合数据层"""
    total_found: int = Field(..., description="本次检索实际找到的片段数")
    results: List[DocumentResult] = Field(..., description="精排后的文档片段列表")
    # 可以在这里增加额外的推理信息，比如：
    # query_vector_id: str = Field(...)

class SearchResponse(BaseModel):
    """知识库搜索接口的顶级返回规范"""
    code: int = Field(default=200)
    message: str = Field(default="success")
    data: SearchResponseData