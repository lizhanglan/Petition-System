from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.core.database import get_db
from app.models.user import User
from app.models.version import Version
from app.models.document import Document
from app.models.audit_log import AuditLog
from app.api.v1.endpoints.auth import get_current_user
from app.services.version_compare_service import version_compare_service
from pydantic import BaseModel

router = APIRouter()

class VersionCreate(BaseModel):
    document_id: int
    content: str
    structured_content: dict
    change_description: Optional[str] = None

class VersionResponse(BaseModel):
    id: int
    document_id: int
    version_number: int
    content: str
    change_description: Optional[str]
    is_rollback: int
    rollback_from_version: Optional[int]
    created_at: datetime

class RollbackRequest(BaseModel):
    document_id: int
    target_version: int
    rollback_reason: Optional[str] = None

class CompareRequest(BaseModel):
    document_id: int
    version1: int
    version2: int
    compare_type: str = 'full'  # 'full', 'text', 'fields'

class CompareResponse(BaseModel):
    version1_number: int
    version2_number: int
    compare_type: str
    text_diff: Optional[Dict[str, Any]] = None
    fields_diff: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any]
    summary: str
    highlights: List[Dict[str, str]]
    compared_at: str

@router.post("/create", response_model=VersionResponse)
async def create_version(
    version_data: VersionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建版本记录"""
    # 验证文档所有权
    result = await db.execute(
        select(Document).where(Document.id == version_data.document_id, Document.user_id == current_user.id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="文书不存在")
    
    # 获取当前最大版本号
    result = await db.execute(
        select(Version.version_number)
        .where(Version.document_id == version_data.document_id)
        .order_by(Version.version_number.desc())
        .limit(1)
    )
    max_version = result.scalar_one_or_none()
    next_version = (max_version or 0) + 1
    
    # 创建版本记录
    version = Version(
        document_id=version_data.document_id,
        user_id=current_user.id,
        version_number=next_version,
        content=version_data.content,
        structured_content=version_data.structured_content,
        change_description=version_data.change_description,
        is_rollback=0
    )
    db.add(version)
    
    # 记录审计日志
    audit_log = AuditLog(
        user_id=current_user.id,
        action="create_version",
        resource_type="version",
        resource_id=version_data.document_id,
        details={"version_number": next_version}
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(version)
    
    return VersionResponse(
        id=version.id,
        document_id=version.document_id,
        version_number=version.version_number,
        content=version.content,
        change_description=version.change_description,
        is_rollback=version.is_rollback,
        rollback_from_version=version.rollback_from_version,
        created_at=version.created_at
    )

@router.get("/list/{document_id}", response_model=List[VersionResponse])
async def list_versions(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取文书版本列表"""
    # 验证文档所有权
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="文书不存在")
    
    # 获取版本列表
    result = await db.execute(
        select(Version)
        .where(Version.document_id == document_id)
        .order_by(Version.version_number.desc())
    )
    versions = result.scalars().all()
    
    return [
        VersionResponse(
            id=v.id,
            document_id=v.document_id,
            version_number=v.version_number,
            content=v.content,
            change_description=v.change_description,
            is_rollback=v.is_rollback,
            rollback_from_version=v.rollback_from_version,
            created_at=v.created_at
        )
        for v in versions
    ]

@router.post("/rollback", response_model=VersionResponse)
async def rollback_version(
    request: RollbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """版本回滚"""
    # 验证文档所有权
    result = await db.execute(
        select(Document).where(Document.id == request.document_id, Document.user_id == current_user.id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="文书不存在")
    
    # 获取目标版本
    result = await db.execute(
        select(Version).where(
            Version.document_id == request.document_id,
            Version.version_number == request.target_version
        )
    )
    target_version = result.scalar_one_or_none()
    
    if not target_version:
        raise HTTPException(status_code=404, detail="目标版本不存在")
    
    # 获取当前最大版本号
    result = await db.execute(
        select(Version.version_number)
        .where(Version.document_id == request.document_id)
        .order_by(Version.version_number.desc())
        .limit(1)
    )
    max_version = result.scalar_one_or_none()
    next_version = (max_version or 0) + 1
    
    # 创建回滚版本
    rollback_version = Version(
        document_id=request.document_id,
        user_id=current_user.id,
        version_number=next_version,
        content=target_version.content,
        structured_content=target_version.structured_content,
        change_description=f"回滚至版本 {request.target_version}：{request.rollback_reason or ''}",
        is_rollback=1,
        rollback_from_version=request.target_version
    )
    db.add(rollback_version)
    
    # 更新文档内容
    document.content = target_version.content
    document.structured_content = target_version.structured_content
    
    # 记录审计日志
    audit_log = AuditLog(
        user_id=current_user.id,
        action="rollback",
        resource_type="version",
        resource_id=request.document_id,
        details={
            "from_version": max_version,
            "to_version": request.target_version,
            "reason": request.rollback_reason
        }
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(rollback_version)
    
    return VersionResponse(
        id=rollback_version.id,
        document_id=rollback_version.document_id,
        version_number=rollback_version.version_number,
        content=rollback_version.content,
        change_description=rollback_version.change_description,
        is_rollback=rollback_version.is_rollback,
        rollback_from_version=rollback_version.rollback_from_version,
        created_at=rollback_version.created_at
    )


@router.post("/compare", response_model=CompareResponse)
async def compare_versions(
    request: CompareRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """版本对比"""
    # 验证文档所有权
    result = await db.execute(
        select(Document).where(Document.id == request.document_id, Document.user_id == current_user.id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="文书不存在")
    
    # 获取两个版本
    result = await db.execute(
        select(Version).where(
            Version.document_id == request.document_id,
            Version.version_number.in_([request.version1, request.version2])
        )
    )
    versions = result.scalars().all()
    
    if len(versions) != 2:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    # 按版本号排序
    versions_dict = {v.version_number: v for v in versions}
    version1 = versions_dict[request.version1]
    version2 = versions_dict[request.version2]
    
    # 准备版本数据
    version1_data = {
        'version_number': version1.version_number,
        'content': version1.content or '',
        'structured_content': version1.structured_content or {},
        'created_at': version1.created_at.isoformat() if version1.created_at else None,
        'change_description': version1.change_description
    }
    
    version2_data = {
        'version_number': version2.version_number,
        'content': version2.content or '',
        'structured_content': version2.structured_content or {},
        'created_at': version2.created_at.isoformat() if version2.created_at else None,
        'change_description': version2.change_description,
        'is_rollback': version2.is_rollback
    }
    
    # 执行对比
    diff_result = version_compare_service.compare_versions(
        version1_data,
        version2_data,
        request.compare_type
    )
    
    # 生成摘要和亮点
    summary = version_compare_service.generate_diff_summary(diff_result)
    highlights = version_compare_service.get_change_highlights(diff_result)
    
    # 记录审计日志
    audit_log = AuditLog(
        user_id=current_user.id,
        action="compare_versions",
        resource_type="version",
        resource_id=request.document_id,
        details={
            "version1": request.version1,
            "version2": request.version2,
            "compare_type": request.compare_type
        }
    )
    db.add(audit_log)
    await db.commit()
    
    return CompareResponse(
        version1_number=diff_result['version1_number'],
        version2_number=diff_result['version2_number'],
        compare_type=diff_result['compare_type'],
        text_diff=diff_result.get('text_diff'),
        fields_diff=diff_result.get('fields_diff'),
        metadata=diff_result['metadata'],
        summary=summary,
        highlights=highlights,
        compared_at=diff_result['compared_at']
    )

@router.get("/{version_id}", response_model=VersionResponse)
async def get_version_detail(
    version_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取版本详情"""
    # 获取版本
    result = await db.execute(
        select(Version).where(Version.id == version_id)
    )
    version = result.scalar_one_or_none()
    
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    # 验证文档所有权
    result = await db.execute(
        select(Document).where(Document.id == version.document_id, Document.user_id == current_user.id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="无权访问此版本")
    
    return VersionResponse(
        id=version.id,
        document_id=version.document_id,
        version_number=version.version_number,
        content=version.content,
        change_description=version.change_description,
        is_rollback=version.is_rollback,
        rollback_from_version=version.rollback_from_version,
        created_at=version.created_at
    )
