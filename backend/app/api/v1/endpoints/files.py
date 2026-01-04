from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import hashlib
from datetime import datetime
from app.core.database import get_db
from app.core.rate_limiter import upload_rate_limit, user_rate_limit
from app.models.user import User
from app.models.file import File
from app.models.audit_log import AuditLog
from app.api.v1.endpoints.auth import get_current_user
from app.core.minio_client import minio_client
from app.services.preview_service_selector import preview_service_selector
from app.core.config import settings
from pydantic import BaseModel

router = APIRouter()

class FileResponse(BaseModel):
    id: int
    file_name: str
    file_type: str
    file_size: int
    status: str
    created_at: datetime
    preview_url: str = None

@router.post("/upload", response_model=FileResponse)
@upload_rate_limit
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    req: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传单个文件"""
    # 验证文件类型
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS_LIST:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型，仅支持：{settings.ALLOWED_EXTENSIONS}")
    
    # 读取文件内容
    file_content = await file.read()
    file_size = len(file_content)
    
    # 验证文件大小
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制（{settings.MAX_UPLOAD_SIZE} 字节）")
    
    # 计算文件哈希
    file_hash = hashlib.sha256(file_content).hexdigest()
    
    # 生成存储路径
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    storage_path = f"uploads/{current_user.id}/{timestamp}_{file.filename}"
    
    # 上传到 MinIO
    content_type = file.content_type or "application/octet-stream"
    success = await minio_client.upload_file(storage_path, file_content, content_type)
    
    if not success:
        raise HTTPException(status_code=500, detail="文件上传失败")
    
    # 保存文件记录
    db_file = File(
        user_id=current_user.id,
        file_name=file.filename,
        file_type=file_ext,
        file_size=file_size,
        storage_path=storage_path,
        file_hash=file_hash,
        status="uploaded"
    )
    db.add(db_file)
    
    # 记录审计日志
    audit_log = AuditLog(
        user_id=current_user.id,
        action="upload",
        resource_type="file",
        details={"file_name": file.filename, "file_size": file_size}
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(db_file)
    
    # 获取预览 URL（优先使用WPS服务）
    file_url = minio_client.get_file_url(storage_path)
    preview_url = ""
    
    if file_url:
        preview_result = await preview_service_selector.get_preview_url(
            file_url=file_url,
            file_name=file.filename,
            user_id=str(current_user.id),
            permission="read"
        )
        if preview_result and preview_result.get("preview_url"):
            preview_url = preview_result["preview_url"]
            print(f"[Upload] Preview service: {preview_result.get('service_type')}")
    
    return FileResponse(
        id=db_file.id,
        file_name=db_file.file_name,
        file_type=db_file.file_type,
        file_size=db_file.file_size,
        status=db_file.status,
        created_at=db_file.created_at,
        preview_url=preview_url or ""
    )

class BatchUploadResult(BaseModel):
    success_count: int
    failed_count: int
    total_count: int
    results: List[dict]

@router.post("/batch-upload", response_model=BatchUploadResult)
@upload_rate_limit
async def batch_upload_files(
    files: List[UploadFile] = FastAPIFile(...),
    req: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量上传文件"""
    results = []
    success_count = 0
    failed_count = 0
    
    for file in files:
        try:
            # 验证文件类型
            file_ext = file.filename.split(".")[-1].lower()
            if file_ext not in settings.ALLOWED_EXTENSIONS_LIST:
                results.append({
                    "file_name": file.filename,
                    "success": False,
                    "error": f"不支持的文件类型"
                })
                failed_count += 1
                continue
            
            # 读取文件内容
            file_content = await file.read()
            file_size = len(file_content)
            
            # 验证文件大小
            if file_size > settings.MAX_UPLOAD_SIZE:
                results.append({
                    "file_name": file.filename,
                    "success": False,
                    "error": f"文件大小超过限制"
                })
                failed_count += 1
                continue
            
            # 计算文件哈希
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # 生成存储路径
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")  # 添加微秒避免冲突
            storage_path = f"uploads/{current_user.id}/{timestamp}_{file.filename}"
            
            # 上传到 MinIO
            content_type = file.content_type or "application/octet-stream"
            success = await minio_client.upload_file(storage_path, file_content, content_type)
            
            if not success:
                results.append({
                    "file_name": file.filename,
                    "success": False,
                    "error": "MinIO 上传失败"
                })
                failed_count += 1
                continue
            
            # 保存文件记录
            db_file = File(
                user_id=current_user.id,
                file_name=file.filename,
                file_type=file_ext,
                file_size=file_size,
                storage_path=storage_path,
                file_hash=file_hash,
                status="uploaded"
            )
            db.add(db_file)
            await db.flush()  # 获取 ID
            
            results.append({
                "file_name": file.filename,
                "success": True,
                "file_id": db_file.id,
                "file_size": file_size
            })
            success_count += 1
            
        except Exception as e:
            results.append({
                "file_name": file.filename,
                "success": False,
                "error": str(e)
            })
            failed_count += 1
    
    # 记录审计日志
    audit_log = AuditLog(
        user_id=current_user.id,
        action="batch_upload",
        resource_type="file",
        details={
            "total_count": len(files),
            "success_count": success_count,
            "failed_count": failed_count
        }
    )
    db.add(audit_log)
    
    await db.commit()
    
    return BatchUploadResult(
        success_count=success_count,
        failed_count=failed_count,
        total_count=len(files),
        results=results
    )

@router.get("/list", response_model=List[FileResponse])
async def list_files(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取文件列表"""
    result = await db.execute(
        select(File)
        .where(File.user_id == current_user.id)
        .order_by(File.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    files = result.scalars().all()
    
    return [
        FileResponse(
            id=f.id,
            file_name=f.file_name,
            file_type=f.file_type,
            file_size=f.file_size,
            status=f.status,
            created_at=f.created_at
        )
        for f in files
    ]

@router.get("/{file_id}/preview")
async def get_file_preview(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取文件预览 URL"""
    try:
        result = await db.execute(
            select(File).where(File.id == file_id, File.user_id == current_user.id)
        )
        file = result.scalar_one_or_none()
        
        if not file:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 获取文件 URL
        file_url = minio_client.get_file_url(file.storage_path)
        if not file_url:
            raise HTTPException(status_code=500, detail="无法获取文件 URL")
        
        # 使用ONLYOFFICE预览（支持docx, doc, xlsx, xls, pptx, ppt, pdf等）
        supported_types = ['docx', 'doc', 'xlsx', 'xls', 'pptx', 'ppt', 'pdf']
        file_ext = file.file_type.lower().lstrip('.')
        
        if file_ext in supported_types:
            print(f"[Preview] Using ONLYOFFICE for {file_ext} file")
            return {
                "preview_url": "use_onlyoffice_component",
                "file_url": file_url,
                "preview_type": "onlyoffice",
                "file_type": file.file_type,
                "file_name": file.file_name
            }
        
        # 不支持的文件类型，尝试使用WPS或华为云
        preview_result = await preview_service_selector.get_preview_url(
            file_url=file_url,
            file_name=file.file_name,
            user_id=str(current_user.id),
            permission="read"
        )
        
        preview_url = preview_result.get("preview_url") if preview_result else None
        service_type = preview_result.get("service_type", "unsupported") if preview_result else "unsupported"
        
        print(f"[Preview] Service: {service_type}, URL: {preview_url}")
        
        return {
            "preview_url": preview_url,
            "file_url": file_url,
            "preview_type": service_type,  # wps, huawei, direct, unsupported
            "file_type": file.file_type,
            "file_name": file.file_name
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Preview error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")

@router.get("/{file_id}/download")
async def download_file_by_id(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载文件"""
    from fastapi.responses import RedirectResponse
    
    result = await db.execute(
        select(File).where(File.id == file_id, File.user_id == current_user.id)
    )
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 获取下载 URL（不使用 inline）
    download_url = minio_client.get_file_url(file.storage_path, inline=False)
    
    if not download_url:
        raise HTTPException(status_code=500, detail="无法生成下载链接")
    
    # 重定向到 MinIO 下载 URL
    return RedirectResponse(url=download_url)

@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除文件"""
    result = await db.execute(
        select(File).where(File.id == file_id, File.user_id == current_user.id)
    )
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 从 MinIO 删除
    await minio_client.delete_file(file.storage_path)
    
    # 从数据库删除
    await db.delete(file)
    
    # 记录审计日志
    audit_log = AuditLog(
        user_id=current_user.id,
        action="delete",
        resource_type="file",
        resource_id=file_id,
        details={"file_name": file.file_name}
    )
    db.add(audit_log)
    
    await db.commit()
    
    return {"message": "文件已删除"}
