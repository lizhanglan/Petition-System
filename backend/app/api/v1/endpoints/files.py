from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import hashlib
from datetime import datetime
from app.core.database import get_db
from app.models.user import User
from app.models.file import File
from app.models.audit_log import AuditLog
from app.api.v1.endpoints.auth import get_current_user
from app.core.minio_client import minio_client
from app.services.office_preview_service import office_preview_service
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
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传文件"""
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
    
    # 获取预览 URL
    file_url = minio_client.get_file_url(storage_path)
    preview_url = await office_preview_service.get_preview_url(file_url) if file_url else ""
    
    return FileResponse(
        id=db_file.id,
        file_name=db_file.file_name,
        file_type=db_file.file_type,
        file_size=db_file.file_size,
        status=db_file.status,
        created_at=db_file.created_at,
        preview_url=preview_url or ""
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
        
        preview_url = None
        preview_type = "direct"  # direct, huawei, unsupported
        
        # 对于 PDF 和 Word 文档，优先尝试华为云服务
        if file.file_type in ['pdf', 'doc', 'docx']:
            print(f"[Preview] 尝试使用华为云预览服务: {file.file_type}")
            preview_url = await office_preview_service.get_preview_url(file_url)
            
            if preview_url:
                preview_type = "huawei"
                print(f"[Preview] 华为云预览成功")
            else:
                print(f"[Preview] 华为云预览失败，使用降级方案")
                # 华为云失败，使用降级方案
                if file.file_type == 'pdf':
                    # PDF 直接返回文件 URL，浏览器可以直接预览
                    preview_url = file_url
                    preview_type = "direct"
                    print(f"[Preview] PDF 使用浏览器直接预览")
                else:
                    # Word 文档不支持预览
                    preview_url = None
                    preview_type = "unsupported"
                    print(f"[Preview] Word 文档暂不支持预览")
        else:
            # 其他格式不支持预览
            preview_url = None
            preview_type = "unsupported"
        
        return {
            "preview_url": preview_url,
            "file_url": file_url,
            "preview_type": preview_type,
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
