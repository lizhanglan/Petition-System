from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)  # upload, review, generate, edit, rollback, etc.
    resource_type = Column(String(50))  # file, document, template
    resource_id = Column(Integer)
    details = Column(JSON)  # 操作详情
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
