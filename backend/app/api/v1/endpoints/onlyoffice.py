"""
ONLYOFFICE API端点
提供编辑器配置、文件下载代理和保存回调功能
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from pydantic import BaseModel
import httpx
import io

from app.core.database import get_db
from app.models.user import User
from app.models.file import File
from app.models.document import Document
from app.api.v1.endpoints.auth import get_current_user
from app.services.onlyoffice_service import onlyoffice_service
from app.core.minio_client import minio_client

router = APIRouter()


class EditorConfigRequest(BaseModel):
    """编辑器配置请求"""
    file_id: Optional[int] = None
    document_id: Optional[int] = None
    mode: str = 'view'  # 'view' or 'edit'


@router.post("/config")
async def get_editor_config(
    request: EditorConfigRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取ONLYOFFICE编辑器配置
    支持文件和文书两种类型
    """
    
    # 验证参数
    if not request.file_id and not request.document_id:
        raise HTTPException(status_code=400, detail="必须提供file_id或document_id")
    
    if request.file_id and request.document_id:
        raise HTTPException(status_code=400, detail="file_id和document_id只能提供一个")
    
    # 处理文件预览/编辑
    if request.file_id:
        # 查询文件
        result = await db.execute(
            select(File).where(
                File.id == request.file_id,
                File.user_id == current_user.id
            )
        )
        file = result.scalar_one_or_none()
        
        if not file:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 生成编辑器配置
        config = await onlyoffice_service.get_editor_config_for_file(
            file_id=file.id,
            file_name=file.file_name,
            file_type=file.file_type,
            user_id=str(current_user.id),
            user_name=current_user.full_name or current_user.username,
            mode=request.mode,
            updated_at=file.updated_at
        )
        
        return config
    
    # 处理文书预览/编辑
    if request.document_id:
        # 查询文书
        result = await db.execute(
            select(Document).where(
                Document.id == request.document_id,
                Document.user_id == current_user.id
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(status_code=404, detail="文书不存在")
        
        # 生成编辑器配置
        config = await onlyoffice_service.get_editor_config_for_document(
            document_id=document.id,
            file_name=document.title + '.docx',
            file_type='docx',
            user_id=str(current_user.id),
            user_name=current_user.full_name or current_user.username,
            mode=request.mode,
            updated_at=document.updated_at
        )
        
        return config


@router.api_route("/download/file/{file_id}", methods=["GET", "HEAD"])
async def download_file_for_onlyoffice(
    file_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    文件下载代理端点（供ONLYOFFICE访问）
    ONLYOFFICE服务器通过此端点下载文件
    注意：此端点不需要认证，因为ONLYOFFICE服务器无法提供用户token
    """
    
    print(f"[OnlyOffice] ========== Download Request ==========")
    print(f"[OnlyOffice] File ID: {file_id}")
    print(f"[OnlyOffice] Client IP: {request.client.host if request.client else 'unknown'}")
    print(f"[OnlyOffice] User-Agent: {request.headers.get('user-agent', 'unknown')}")
    print(f"[OnlyOffice] Headers: {dict(request.headers)}")
    
    # 查询文件
    result = await db.execute(
        select(File).where(File.id == file_id)
    )
    file = result.scalar_one_or_none()
    
    if not file:
        print(f"[OnlyOffice] ERROR: File {file_id} not found in database")
        raise HTTPException(status_code=404, detail="文件不存在")
    
    print(f"[OnlyOffice] File found: {file.file_name}")
    print(f"[OnlyOffice] Storage path: {file.storage_path}")
    print(f"[OnlyOffice] File type: {file.file_type}")
    
    # 根据文件类型确定MIME类型
    mime_types = {
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'ppt': 'application/vnd.ms-powerpoint',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    }
    content_type = mime_types.get(file.file_type.lower(), 'application/octet-stream')
    print(f"[OnlyOffice] Content type: {content_type}")
    
    # 对文件名进行URL编码以支持中文
    from urllib.parse import quote
    encoded_filename = quote(file.file_name)
    
    # 如果是HEAD请求，只返回头部信息
    if request.method == "HEAD":
        print(f"[OnlyOffice] HEAD request - returning headers only")
        return StreamingResponse(
            io.BytesIO(b""),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
                "Access-Control-Allow-Headers": "*"
            }
        )
    
    try:
        # 从MinIO下载文件
        print(f"[OnlyOffice] Downloading from MinIO...")
        file_data = await minio_client.download_file(file.storage_path)
        
        print(f"[OnlyOffice] SUCCESS: File downloaded from MinIO, size: {len(file_data)} bytes")
        
        # 对文件名进行URL编码以支持中文
        from urllib.parse import quote
        encoded_filename = quote(file.file_name)
        
        # 返回文件流
        return StreamingResponse(
            io.BytesIO(file_data),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
                "Content-Length": str(len(file_data)),
                "Access-Control-Allow-Origin": "*",  # 允许跨域
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*"
            }
        )
    except Exception as e:
        print(f"[OnlyOffice] ERROR downloading file: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"文件下载失败: {str(e)}")


@router.api_route("/download/document/{document_id}", methods=["GET", "HEAD"])
async def download_document_for_onlyoffice(
    document_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    文书下载代理端点（供ONLYOFFICE访问）
    ONLYOFFICE服务器通过此端点下载文书
    注意：此端点不需要认证，因为ONLYOFFICE服务器无法提供用户token
    """
    
    print(f"[OnlyOffice] ========== Download Request ==========")
    print(f"[OnlyOffice] Document ID: {document_id}")
    print(f"[OnlyOffice] Client IP: {request.client.host if request.client else 'unknown'}")
    print(f"[OnlyOffice] User-Agent: {request.headers.get('user-agent', 'unknown')}")
    
    # 查询文书
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        print(f"[OnlyOffice] ERROR: Document {document_id} not found in database")
        raise HTTPException(status_code=404, detail="文书不存在")
    
    print(f"[OnlyOffice] Document found: {document.title}")
    print(f"[OnlyOffice] Storage path: {document.file_path}")
    
    # 对文件名进行URL编码以支持中文
    from urllib.parse import quote
    encoded_filename = quote(f"{document.title}.docx")
    
    # 如果是HEAD请求，只返回头部信息
    if request.method == "HEAD":
        print(f"[OnlyOffice] HEAD request - returning headers only")
        return StreamingResponse(
            io.BytesIO(b""),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
                "Access-Control-Allow-Headers": "*"
            }
        )
    
    try:
        # 从MinIO下载文书
        print(f"[OnlyOffice] Downloading from MinIO...")
        file_data = await minio_client.download_file(document.file_path)
        
        print(f"[OnlyOffice] SUCCESS: Document downloaded from MinIO, size: {len(file_data)} bytes")
        
        # 返回文件流
        return StreamingResponse(
            io.BytesIO(file_data),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
                "Content-Length": str(len(file_data)),
                "Access-Control-Allow-Origin": "*",  # 允许跨域
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*"
            }
        )
    except Exception as e:
        print(f"[OnlyOffice] ERROR downloading document: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"文书下载失败: {str(e)}")


@router.post("/callback")
async def handle_callback(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    处理ONLYOFFICE保存回调
    当用户编辑完成后，ONLYOFFICE会调用此端点保存文件
    """
    
    # 获取回调数据
    callback_data = await request.json()
    
    print(f"[OnlyOffice] Callback received: {callback_data}")
    
    # 从查询参数获取ID和类型
    file_id = request.query_params.get('fileId')
    document_id = request.query_params.get('documentId')
    content_type = request.query_params.get('type')
    
    if not file_id and not document_id:
        return {"error": 1, "message": "File ID or Document ID not provided"}
    
    # 处理回调
    result = await onlyoffice_service.handle_callback(
        callback_data,
        file_id=int(file_id) if file_id else None,
        document_id=int(document_id) if document_id else None
    )
    
    # 如果需要保存文件
    if result.get('download_url'):
        download_url = result['download_url']
        
        try:
            # 从ONLYOFFICE下载编辑后的文件
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(download_url)
                if response.status_code == 200:
                    file_bytes = response.content
                    
                    # 保存文件
                    if file_id:
                        # 更新文件
                        db_result = await db.execute(
                            select(File).where(File.id == int(file_id))
                        )
                        file = db_result.scalar_one_or_none()
                        
                        if file:
                            # 上传到MinIO（覆盖原文件）
                            await minio_client.upload_file(
                                file.storage_path,
                                file_bytes,
                                file.content_type
                            )
                            
                            # 更新文件记录
                            file.file_size = len(file_bytes)
                            await db.commit()
                            
                            print(f"[OnlyOffice] File {file_id} saved successfully")
                    
                    elif document_id:
                        # 更新文书
                        db_result = await db.execute(
                            select(Document).where(Document.id == int(document_id))
                        )
                        document = db_result.scalar_one_or_none()
                        
                        if document:
                            # 上传到MinIO（覆盖原文件）
                            await minio_client.upload_file(
                                document.file_path,
                                file_bytes,
                                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
                            
                            # 更新文书记录
                            document.file_size = len(file_bytes)
                            await db.commit()
                            
                            print(f"[OnlyOffice] Document {document_id} saved successfully")
                else:
                    print(f"[OnlyOffice] Failed to download from ONLYOFFICE: {response.status_code}")
                    return {"error": 1, "message": "Failed to download edited file"}
        except Exception as e:
            print(f"[OnlyOffice] Error saving file: {e}")
            import traceback
            traceback.print_exc()
            return {"error": 1, "message": f"Save failed: {str(e)}"}
    
    return result


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "onlyoffice_enabled": onlyoffice_service.jwt_enabled,
        "server_url": onlyoffice_service.server_url,
        "backend_public_url": onlyoffice_service.backend_public_url
    }
