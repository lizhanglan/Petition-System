from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File as FastAPIFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
import json
from app.core.database import get_db
from app.core.rate_limiter import ai_rate_limit, user_rate_limit
from app.core.minio_client import minio_client
from app.models.user import User
from app.models.template import Template
from app.models.audit_log import AuditLog
from app.api.v1.endpoints.auth import get_current_user
from app.services.template_processor_service import template_processor_service
from app.services.docx_render_service import docx_render_service
from pydantic import BaseModel

router = APIRouter()


# ==================== 请求/响应模型 ====================

class TemplateResponse(BaseModel):
    """模板响应"""
    id: int
    name: str
    document_type: str
    fields: Optional[dict] = None
    template_file_path: Optional[str] = None
    is_active: bool
    version: int
    created_at: datetime

    class Config:
        from_attributes = True


class TemplatePreviewResponse(BaseModel):
    """模板预览响应（AI处理后）"""
    success: bool
    fields: Optional[dict] = None
    replacements: Optional[dict] = None
    original_text: Optional[str] = None
    error: Optional[str] = None
    # 临时文件路径，用于后续确认保存
    temp_template_path: Optional[str] = None
    temp_original_path: Optional[str] = None


class TemplateConfirmRequest(BaseModel):
    """确认保存模板请求"""
    name: str
    document_type: str
    temp_template_path: str
    temp_original_path: str
    fields: dict


# ==================== API 端点 ====================

@router.post("/upload")
@ai_rate_limit
async def upload_and_process_template(
    file: UploadFile = FastAPIFile(...),
    req: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传 Word 文档并进行 AI 处理
    
    流程：
    1. 上传 Word 文档
    2. AI 识别可变字段
    3. 自动替换为占位符
    4. 返回预览数据供用户确认
    """
    # 验证文件类型
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["docx", "doc"]:
        raise HTTPException(status_code=400, detail="仅支持 Word 文档 (.docx, .doc)")
    
    try:
        # 读取文件内容
        file_bytes = await file.read()
        print(f"[TemplateUpload] File uploaded: {file.filename}, {len(file_bytes)} bytes")
        
        # 调用模板处理服务
        result = await template_processor_service.process_template(file_bytes, file.filename)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "模板处理失败"))
        
        # 生成临时文件路径
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        temp_template_path = f"temp_templates/{current_user.id}/{timestamp}_template.docx"
        temp_original_path = f"temp_templates/{current_user.id}/{timestamp}_original.docx"
        
        # 上传临时文件到 MinIO
        await minio_client.upload_file(
            temp_template_path,
            result["template_bytes"],
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        await minio_client.upload_file(
            temp_original_path,
            file_bytes,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        print(f"[TemplateUpload] Temp files saved: {temp_template_path}")
        
        return TemplatePreviewResponse(
            success=True,
            fields=result.get("fields"),
            replacements=result.get("replacements"),
            original_text=result.get("original_text", "")[:1000],  # 只返回前1000字符
            temp_template_path=temp_template_path,
            temp_original_path=temp_original_path
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[TemplateUpload] Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"模板处理失败: {str(e)}")


@router.get("/temp-preview")
async def get_temp_preview(
    path: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取临时模板文件内容（用于前端 docx-preview 预览）
    """
    # 验证路径属于当前用户
    if not path.startswith(f"temp_templates/{current_user.id}/"):
        raise HTTPException(status_code=403, detail="无权访问此文件")
    
    try:
        file_bytes = await minio_client.download_file(path)
        if not file_bytes:
            raise HTTPException(status_code=404, detail="文件不存在或已过期")
        
        return Response(
            content=file_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'inline; filename="preview.docx"'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[TempPreview] Error: {e}")
        raise HTTPException(status_code=500, detail="获取预览失败")


@router.post("/confirm", response_model=TemplateResponse)
async def confirm_template(
    request: TemplateConfirmRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    确认并保存模板
    
    用户预览 AI 处理结果后，调用此接口正式保存模板
    """
    try:
        # 移动临时文件到正式位置
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        final_template_path = f"templates/{current_user.id}/{timestamp}_{request.name}.docx"
        final_original_path = f"templates/{current_user.id}/{timestamp}_{request.name}_original.docx"
        
        # 下载临时文件
        template_bytes = await minio_client.download_file(request.temp_template_path)
        original_bytes = await minio_client.download_file(request.temp_original_path)
        
        if not template_bytes or not original_bytes:
            raise HTTPException(status_code=400, detail="临时文件已过期，请重新上传")
        
        # 上传到正式位置
        await minio_client.upload_file(
            final_template_path,
            template_bytes,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        await minio_client.upload_file(
            final_original_path,
            original_bytes,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        # 删除临时文件
        await minio_client.delete_file(request.temp_template_path)
        await minio_client.delete_file(request.temp_original_path)
        
        # 创建模板记录
        template = Template(
            user_id=current_user.id,
            name=request.name,
            document_type=request.document_type,
            template_file_path=final_template_path,
            original_file_path=final_original_path,
            fields=request.fields,
            is_active=True,
            version=1
        )
        db.add(template)
        
        # 记录审计日志
        audit_log = AuditLog(
            user_id=current_user.id,
            action="create_template",
            resource_type="template",
            details={
                "name": request.name,
                "document_type": request.document_type,
                "field_count": len(request.fields)
            }
        )
        db.add(audit_log)
        
        await db.commit()
        await db.refresh(template)
        
        print(f"[TemplateConfirm] Template saved: ID={template.id}, name={request.name}")
        
        return TemplateResponse(
            id=template.id,
            name=template.name,
            document_type=template.document_type,
            fields=template.fields,
            template_file_path=template.template_file_path,
            is_active=template.is_active,
            version=template.version,
            created_at=template.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[TemplateConfirm] Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"模板保存失败: {str(e)}")


@router.get("/list", response_model=List[TemplateResponse])
async def list_templates(
    document_type: str = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模板列表"""
    query = select(Template).where(
        Template.user_id == current_user.id, 
        Template.is_active == True
    )
    
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
            fields=t.fields or {},
            template_file_path=t.template_file_path,
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
        fields=template.fields or {},
        template_file_path=template.template_file_path,
        is_active=template.is_active,
        version=template.version,
        created_at=template.created_at
    )


@router.get("/{template_id}/preview")
async def preview_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模板预览（下载模板文件）"""
    result = await db.execute(
        select(Template).where(Template.id == template_id, Template.user_id == current_user.id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    if not template.template_file_path:
        raise HTTPException(status_code=400, detail="模板文件不存在")
    
    # 下载模板文件
    file_bytes = await minio_client.download_file(template.template_file_path)
    if not file_bytes:
        raise HTTPException(status_code=500, detail="模板文件下载失败")
    
    from urllib.parse import quote
    filename = f"{template.name}.docx"
    encoded_filename = quote(filename)
    
    return Response(
        content=file_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"
        }
    )


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除模板（软删除）"""
    result = await db.execute(
        select(Template).where(Template.id == template_id, Template.user_id == current_user.id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 软删除
    template.is_active = False
    
    # 记录审计日志
    audit_log = AuditLog(
        user_id=current_user.id,
        action="delete_template",
        resource_type="template",
        resource_id=template_id,
        details={"name": template.name}
    )
    db.add(audit_log)
    
    await db.commit()
    
    return {"success": True, "message": "模板已删除"}
