from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime
from app.core.database import get_db
from app.models.user import User
from app.models.template import Template
from app.models.audit_log import AuditLog
from app.api.v1.endpoints.auth import get_current_user
from pydantic import BaseModel

router = APIRouter()

class TemplateCreate(BaseModel):
    name: str
    document_type: str
    structure: dict
    content_template: str
    fields: dict

class TemplateResponse(BaseModel):
    id: int
    name: str
    document_type: str
    structure: dict
    fields: dict
    is_active: bool
    version: int
    created_at: datetime

@router.post("/create", response_model=TemplateResponse)
async def create_template(
    template_data: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建模板"""
    template = Template(
        user_id=current_user.id,
        name=template_data.name,
        document_type=template_data.document_type,
        structure=template_data.structure,
        content_template=template_data.content_template,
        fields=template_data.fields,
        is_active=True,
        version=1
    )
    db.add(template)
    
    # 记录审计日志
    audit_log = AuditLog(
        user_id=current_user.id,
        action="create_template",
        resource_type="template",
        details={"name": template_data.name, "document_type": template_data.document_type}
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(template)
    
    return TemplateResponse(
        id=template.id,
        name=template.name,
        document_type=template.document_type,
        structure=template.structure,
        fields=template.fields,
        is_active=template.is_active,
        version=template.version,
        created_at=template.created_at
    )

@router.get("/list", response_model=List[TemplateResponse])
async def list_templates(
    document_type: str = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模板列表"""
    query = select(Template).where(Template.user_id == current_user.id, Template.is_active == True)
    
    if document_type:
        query = query.where(Template.document_type == document_type)
    
    query = query.order_by(Template.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    templates = result.scalars().all()
    
    return [
        TemplateResponse(
            id=t.id,
            name=t.name,
            document_type=t.document_type,
            structure=t.structure,
            fields=t.fields,
            is_active=t.is_active,
            version=t.version,
            created_at=t.created_at
        )
        for t in templates
    ]

@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模板详情"""
    result = await db.execute(
        select(Template).where(Template.id == template_id, Template.user_id == current_user.id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    return TemplateResponse(
        id=template.id,
        name=template.name,
        document_type=template.document_type,
        structure=template.structure,
        fields=template.fields,
        is_active=template.is_active,
        version=template.version,
        created_at=template.created_at
    )
