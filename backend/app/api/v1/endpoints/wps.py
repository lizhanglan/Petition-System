"""
WPS文档处理API端点
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.user import User
from app.models.document import Document
from app.models.file import File
from app.api.v1.endpoints.auth import get_current_user
from app.services.wps_service import wps_service
from app.core.minio_client import minio_client
from app.core.config import settings

router = APIRouter()


class WPSPreviewRequest(BaseModel):
    file_id: Optional[int] = None
    document_id: Optional[int] = None


class WPSEditRequest(BaseModel):
    document_id: int


class WPSSaveCallbackRequest(BaseModel):
    file_url: str
    user_id: str
    document_id: Optional[int] = None
    signature: str


@router.post("/preview")
async def get_wps_preview_url(
    request: WPSPreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取WPS预览URL
    
    可以预览文件或文书
    """
    if not settings.WPS_ENABLED:
        raise HTTPException(status_code=503, detail="WPS服务未启用")
    
    file_url = None
    file_name = None
    
    # 如果提供了file_id，预览文件
    if request.file_id:
        result = await db.execute(
            select(File).where(File.id == request.file_id, File.user_id == current_user.id)
        )
        file = result.scalar_one_or_none()
        
        if not file:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 获取文件URL
        file_url = minio_client.get_file_url(file.storage_path, expires=3600, inline=True)
        file_name = file.file_name
    
    # 如果提供了document_id，预览文书
    elif request.document_id:
        result = await db.execute(
            select(Document).where(Document.id == request.document_id, Document.user_id == current_user.id)
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(status_code=404, detail="文书不存在")
        
        # 生成临时DOCX文件
        from app.services.document_export_service import document_export_service
        
        docx_bytes = await document_export_service.export_to_docx(
            content=document.content,
            title=document.title,
            options={"document_type": document.document_type}
        )
        
        # 上传到MinIO
        temp_filename = f"temp_preview/{current_user.id}/{document.id}.docx"
        await minio_client.upload_file(
            temp_filename,
            docx_bytes,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        file_url = minio_client.get_file_url(temp_filename, expires=3600, inline=True)
        file_name = f"{document.title}.docx"
    
    else:
        raise HTTPException(status_code=400, detail="请提供file_id或document_id")
    
    if not file_url:
        raise HTTPException(status_code=500, detail="无法获取文件URL")
    
    # 调用WPS服务获取预览URL
    preview_url = await wps_service.get_preview_url(
        file_url=file_url,
        file_name=file_name,
        user_id=str(current_user.id),
        permission="read"
    )
    
    if not preview_url:
        raise HTTPException(status_code=500, detail="获取WPS预览URL失败")
    
    return {
        "preview_url": preview_url,
        "file_url": file_url,
        "file_name": file_name
    }


@router.post("/edit")
async def get_wps_edit_url(
    request: WPSEditRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取WPS编辑URL
    
    用于在线编辑文书
    """
    if not settings.WPS_ENABLED:
        raise HTTPException(status_code=503, detail="WPS服务未启用")
    
    # 获取文书
    result = await db.execute(
        select(Document).where(Document.id == request.document_id, Document.user_id == current_user.id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="文书不存在")
    
    # 生成临时DOCX文件
    from app.services.document_export_service import document_export_service
    
    docx_bytes = await document_export_service.export_to_docx(
        content=document.content,
        title=document.title,
        options={"document_type": document.document_type}
    )
    
    # 上传到MinIO
    temp_filename = f"temp_edit/{current_user.id}/{document.id}.docx"
    await minio_client.upload_file(
        temp_filename,
        docx_bytes,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    
    file_url = minio_client.get_file_url(temp_filename, expires=3600, inline=True)
    file_name = f"{document.title}.docx"
    
    # 构建回调URL
    callback_url = f"{settings.BACKEND_HOST}:{settings.BACKEND_PORT}/api/v1/wps/callback"
    
    # 调用WPS服务获取编辑URL
    edit_data = await wps_service.get_edit_url(
        file_url=file_url,
        file_name=file_name,
        user_id=str(current_user.id),
        user_name=current_user.username,
        callback_url=callback_url
    )
    
    if not edit_data:
        raise HTTPException(status_code=500, detail="获取WPS编辑URL失败")
    
    return {
        "edit_url": edit_data["edit_url"],
        "token": edit_data["token"],
        "expires_in": edit_data["expires_in"],
        "document_id": document.id
    }


@router.post("/callback")
async def wps_save_callback(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    WPS保存回调
    
    当用户在WPS中保存文档时，WPS会调用此接口
    """
    try:
        data = await request.json()
        
        # 处理回调
        success = await wps_service.handle_save_callback(data)
        
        if success:
            return {"code": 0, "message": "success"}
        else:
            return {"code": 1, "message": "failed"}
            
    except Exception as e:
        print(f"[WPS Callback] Error: {e}")
        return {"code": 1, "message": str(e)}
