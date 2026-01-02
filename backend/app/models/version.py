from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.core.database import Base

class Version(Base):
    __tablename__ = "versions"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    content = Column(Text)
    structured_content = Column(JSON)
    change_description = Column(Text)  # 修改说明
    diff_data = Column(JSON)  # 差异数据
    is_rollback = Column(Integer, default=0)  # 是否为回滚版本
    rollback_from_version = Column(Integer, nullable=True)  # 回滚来源版本
    created_at = Column(DateTime(timezone=True), server_default=func.now())
