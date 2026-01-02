from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.core.database import Base

class File(Base):
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf, doc, docx
    file_size = Column(BigInteger, nullable=False)
    storage_path = Column(String(500), nullable=False)  # MinIO 存储路径
    file_hash = Column(String(64))  # 文件哈希值
    status = Column(String(20), default="uploaded")  # uploaded, reviewed, generated
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
