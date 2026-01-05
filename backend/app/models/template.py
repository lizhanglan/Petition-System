from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func
from app.core.database import Base

class Template(Base):
    __tablename__ = "templates"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    document_type = Column(String(50), nullable=False, index=True)
    
    # Word 模板文件路径（MinIO）
    template_file_path = Column(String(500))  # 处理后的模板文件（含占位符）
    original_file_path = Column(String(500))  # 原始上传文件
    
    # 字段定义 JSON
    # 格式: {"variable_name": {"label": "中文名", "type": "text", "required": true}}
    fields = Column(JSON)
    
    # 兼容旧字段（将弃用）
    structure = Column(JSON, nullable=True)
    content_template = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

