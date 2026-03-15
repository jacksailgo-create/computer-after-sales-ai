from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from knowledge_platform_backend.api.database import Base

class DocumentRecord(Base):
    __tablename__ = "kb_documents"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    # 状态枚举: pending(待处理), parsing(解析中), processed(已向量化), error(失败)
    status = Column(String(50), default="pending")
    # 存储解析后、供管理员预览和修改的纯文本(Markdown)
    parsed_content = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)