from pydantic import BaseModel

# ==========================================
# Pydantic 请求与响应模型
# ==========================================

class UserSessionRequest(BaseModel):
    user_id: str

class QueryContext(BaseModel):
    user_id: str
    session_id: str

class QueryRequest(BaseModel):
    query: str
    context: QueryContext