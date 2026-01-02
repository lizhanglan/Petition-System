from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.core.database import Base

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=True)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=True)
    title = Column(String(255), nullable=False)
    content = Column(Text)  # 文书正文内容
    structured_content = Column(JSON)  # 结构化内容（字段+值）
    document_type = Column(String(50))  # 文书类型
    status = Column(String(20), default="draft")  # draft, reviewed, finalized
    classification = Column(String(20), default="public")  # 密级：public, internal, confidential, secret, top_secret
    ai_annotations = Column(JSON)  # AI 标注信息
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
