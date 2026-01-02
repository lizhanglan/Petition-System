from minio import Minio
from minio.error import S3Error
from app.core.config import settings
from datetime import timedelta
import io

class MinIOClient:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """确保存储桶存在"""
        try:
            if not self.client.bucket_exists(settings.MINIO_BUCKET):
                self.client.make_bucket(settings.MINIO_BUCKET)
        except S3Error as e:
            print(f"MinIO bucket error: {e}")
    
    async def upload_file(self, file_name: str, file_data: bytes, content_type: str):
        """上传文件"""
        try:
            self.client.put_object(
                settings.MINIO_BUCKET,
                file_name,
                io.BytesIO(file_data),
                length=len(file_data),
                content_type=content_type
            )
            return True
        except S3Error as e:
            print(f"Upload error: {e}")
            return False
    
    async def download_file(self, file_name: str):
        """下载文件"""
        try:
            response = self.client.get_object(settings.MINIO_BUCKET, file_name)
            return response.read()
        except S3Error as e:
            print(f"Download error: {e}")
            return None
    
    async def delete_file(self, file_name: str):
        """删除文件"""
        try:
            self.client.remove_object(settings.MINIO_BUCKET, file_name)
            return True
        except S3Error as e:
            print(f"Delete error: {e}")
            return False
    
    def get_file_url(self, file_name: str, expires: int = 3600, inline: bool = True):
        """获取文件预签名URL
        
        Args:
            file_name: 文件名
            expires: 过期时间（秒）
            inline: True=在线预览，False=下载
        """
        try:
            response_headers = {}
            if inline:
                # 强制浏览器在线显示而不是下载
                response_headers['response-content-disposition'] = 'inline'
            
            return self.client.presigned_get_object(
                settings.MINIO_BUCKET,
                file_name,
                expires=timedelta(seconds=expires),
                response_headers=response_headers if response_headers else None
            )
        except S3Error as e:
            print(f"Get URL error: {e}")
            return None

minio_client = MinIOClient()
