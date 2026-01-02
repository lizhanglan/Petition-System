from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
import json
from app.core.database import get_db
from app.core.rate_limiter import ai_rate_limit, user_rate_limit
from app.models.user import User
from app.models.template import Template
from app.models.audit_log import AuditLog
from app.models.file import File
from app.api.v1.endpoints.auth import get_current_user
from app.services.deepseek_service import deepseek_service
from app.services.file_parser_service import file_parser_service
from pydantic import BaseModel

router = APIRouter()

class TemplateCreate(BaseModel):
    name: str
    document_type: str
    structure: dict
    content_template: str
    fields: dict

class TemplateExtractRequest(BaseModel):
    file_id: int
    auto_save: bool = False

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

@router.post("/extract")
@ai_rate_limit
async def extract_template(
    request: TemplateExtractRequest,
    req: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从文件中提取模板结构"""
    # 查询文件
    result = await db.execute(
        select(File).where(File.id == request.file_id, File.user_id == current_user.id)
    )
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    try:
        # 解析文件内容
        print(f"[TemplateExtract] Parsing file: {file.filename}")
        parsed_content = await file_parser_service.parse_file(
            file.minio_path,
            file.file_type
        )
        
        if not parsed_content or not parsed_content.get("text"):
            raise HTTPException(status_code=400, detail="文件内容解析失败")
        
        # 调用 AI 提取模板
        print(f"[TemplateExtract] Calling AI to extract template")
        ai_result = await deepseek_service.extract_template(
            parsed_content["text"],
            file.file_type
        )
        
        if not ai_result:
            raise HTTPException(status_code=500, detail="AI 模板提取失败")
        
        # 解析 AI 返回的 JSON
        try:
            template_data = json.loads(ai_result)
        except json.JSONDecodeError:
            # 如果 AI 返回的不是纯 JSON，尝试提取 JSON 部分
            import re
            json_match = re.search(r'\{.*\}', ai_result, re.DOTALL)
            if json_match:
                template_data = json.loads(json_match.group())
            else:
                raise HTTPException(status_code=500, detail="AI 返回格式错误")
        
        # 如果需要自动保存
        if request.auto_save:
            template = Template(
                user_id=current_user.id,
                name=f"{file.filename} - 提取模板",
                document_type=template_data.get("document_type", "未知类型"),
                structure=template_data.get("structure", {}),
                content_template=parsed_content["text"],
                fields=template_data.get("fields", {}),
                is_active=True,
                version=1
            )
            db.add(template)
            
            # 记录审计日志
            audit_log = AuditLog(
                user_id=current_user.id,
                action="extract_template",
                resource_type="template",
                resource_id=file.id,
                details={
                    "file_name": file.filename,
                    "document_type": template_data.get("document_type"),
                    "auto_save": True
                }
            )
            db.add(audit_log)
            
            await db.commit()
            await db.refresh(template)
            
            return {
                "success": True,
                "message": "模板提取并保存成功",
                "template_id": template.id,
                "template_data": template_data
            }
        else:
            # 仅返回提取结果，不保存
            audit_log = AuditLog(
                user_id=current_user.id,
                action="extract_template",
                resource_type="template",
                resource_id=file.id,
                details={
                    "file_name": file.filename,
                    "document_type": template_data.get("document_type"),
                    "auto_save": False
                }
            )
            db.add(audit_log)
            await db.commit()
            
            return {
                "success": True,
                "message": "模板提取成功",
                "template_data": template_data
            }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[TemplateExtract] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"模板提取失败: {str(e)}")

@router.post("/save-extracted")
async def save_extracted_template(
    template_data: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """保存提取的模板（用于手动确认后保存）"""
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
        action="save_extracted_template",
        resource_type="template",
        details={
            "name": template_data.name,
            "document_type": template_data.document_type
        }
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(template)
    
    return {
        "success": True,
        "message": "模板保存成功",
        "template_id": template.id
    }
