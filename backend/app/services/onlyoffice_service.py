"""
ONLYOFFICE文档服务（无JWT版本）
提供文档预览和编辑功能
"""
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
from app.core.config import settings


class OnlyOfficeService:
    """ONLYOFFICE文档服务（无JWT版本）"""
    
    def __init__(self):
        self.server_url = settings.ONLYOFFICE_SERVER_URL
        self.callback_url = settings.ONLYOFFICE_CALLBACK_URL
        self.backend_public_url = settings.BACKEND_PUBLIC_URL
        self.jwt_enabled = settings.ONLYOFFICE_JWT_ENABLED
        
        # 调试日志
        print(f"[OnlyOfficeService] Initialized with:")
        print(f"  - server_url: {self.server_url}")
        print(f"  - callback_url: {self.callback_url}")
        print(f"  - backend_public_url: {self.backend_public_url}")
        print(f"  - jwt_enabled: {self.jwt_enabled}")
    
    def generate_document_key(self, file_id: int, updated_at: datetime) -> str:
        """生成文档唯一key（用于缓存和版本控制）"""
        key_string = f"{file_id}_{updated_at.timestamp()}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get_document_type(self, file_extension: str) -> str:
        """根据文件扩展名获取文档类型"""
        ext = file_extension.lower().lstrip('.')
        
        word_exts = ['doc', 'docx', 'docm', 'dot', 'dotx', 'dotm', 'odt', 'fodt', 'ott', 'rtf', 'txt', 'html', 'htm', 'mht', 'pdf', 'djvu', 'fb2', 'epub', 'xps']
        cell_exts = ['xls', 'xlsx', 'xlsm', 'xlt', 'xltx', 'xltm', 'ods', 'fods', 'ots', 'csv']
        slide_exts = ['pps', 'ppsx', 'ppsm', 'ppt', 'pptx', 'pptm', 'pot', 'potx', 'potm', 'odp', 'fodp', 'otp']
        
        if ext in word_exts:
            return 'word'
        elif ext in cell_exts:
            return 'cell'
        elif ext in slide_exts:
            return 'slide'
        else:
            return 'word'  # 默认
    
    async def get_editor_config_for_file(
        self,
        file_id: int,
        file_name: str,
        file_type: str,
        user_id: str,
        user_name: str,
        mode: str = 'view',
        updated_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        生成文件的ONLYOFFICE编辑器配置
        
        Args:
            file_id: 文件ID
            file_name: 文件名
            file_type: 文件类型（扩展名）
            user_id: 用户ID
            user_name: 用户名
            mode: 模式 ('view' 或 'edit')
            updated_at: 文件更新时间
        
        Returns:
            编辑器配置字典
        """
        if updated_at is None:
            updated_at = datetime.now()
        
        # 生成文档key
        document_key = self.generate_document_key(file_id, updated_at)
        
        # 获取文档类型
        document_type = self.get_document_type(file_type)
        
        # 使用后端代理URL（ONLYOFFICE通过后端下载文件）
        file_url = f"{self.backend_public_url}/api/v1/onlyoffice/download/file/{file_id}"
        
        print(f"[OnlyOfficeService] Generated file URL: {file_url}")
        print(f"  - backend_public_url: {self.backend_public_url}")
        print(f"  - file_id: {file_id}")
        
        # 配置（无JWT版本，更简单）
        config = {
            "document": {
                "fileType": file_type.lower().lstrip('.'),
                "key": document_key,
                "title": file_name,
                "url": file_url,
                "permissions": {
                    "edit": mode == 'edit',
                    "download": True,
                    "print": True,
                    "review": mode == 'edit',
                    "comment": mode == 'edit'
                }
            },
            "documentType": document_type,
            "editorConfig": {
                "mode": mode,
                "lang": "zh-CN",
                "callbackUrl": f"{self.callback_url}?fileId={file_id}&type=file",
                "user": {
                    "id": str(user_id),
                    "name": user_name
                },
                "customization": {
                    "autosave": True,
                    "forcesave": True,
                    "comments": mode == 'edit',
                    "chat": False,
                    "compactHeader": False,
                    "feedback": False,
                    "help": False,
                    "hideRightMenu": False,
                    "plugins": True,
                    "toolbarNoTabs": False,
                    "uiTheme": "theme-light"
                }
            }
        }
        
        return config
    
    async def get_editor_config_for_document(
        self,
        document_id: int,
        file_name: str,
        file_type: str,
        user_id: str,
        user_name: str,
        mode: str = 'view',
        updated_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        生成文书的ONLYOFFICE编辑器配置
        
        Args:
            document_id: 文书ID
            file_name: 文件名
            file_type: 文件类型（扩展名）
            user_id: 用户ID
            user_name: 用户名
            mode: 模式 ('view' 或 'edit')
            updated_at: 文档更新时间
        
        Returns:
            编辑器配置字典
        """
        if updated_at is None:
            updated_at = datetime.now()
        
        # 生成文档key
        document_key = self.generate_document_key(document_id, updated_at)
        
        # 获取文档类型
        document_type = self.get_document_type(file_type)
        
        # 使用后端代理URL（ONLYOFFICE通过后端下载文档）
        file_url = f"{self.backend_public_url}/api/v1/onlyoffice/download/document/{document_id}"
        
        print(f"[OnlyOfficeService] Generated document URL: {file_url}")
        print(f"  - backend_public_url: {self.backend_public_url}")
        print(f"  - document_id: {document_id}")
        
        # 配置（无JWT版本）
        config = {
            "document": {
                "fileType": file_type.lower().lstrip('.'),
                "key": document_key,
                "title": file_name,
                "url": file_url,
                "permissions": {
                    "edit": mode == 'edit',
                    "download": True,
                    "print": True,
                    "review": mode == 'edit',
                    "comment": mode == 'edit'
                }
            },
            "documentType": document_type,
            "editorConfig": {
                "mode": mode,
                "lang": "zh-CN",
                "callbackUrl": f"{self.callback_url}?documentId={document_id}&type=document",
                "user": {
                    "id": str(user_id),
                    "name": user_name
                },
                "customization": {
                    "autosave": True,
                    "forcesave": True,
                    "comments": mode == 'edit',
                    "chat": False,
                    "compactHeader": False,
                    "feedback": False,
                    "help": False,
                    "hideRightMenu": False,
                    "plugins": True,
                    "toolbarNoTabs": False,
                    "uiTheme": "theme-light"
                }
            }
        }
        
        return config
    
    async def handle_callback(
        self,
        callback_data: Dict[str, Any],
        file_id: Optional[int] = None,
        document_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        处理ONLYOFFICE保存回调
        
        回调状态：
        0 - 文档未找到
        1 - 文档正在编辑
        2 - 文档准备保存
        3 - 文档保存错误
        4 - 文档关闭无变化
        6 - 文档正在编辑，但保存当前状态
        7 - 强制保存错误
        
        Args:
            callback_data: 回调数据
            file_id: 文件ID（可选）
            document_id: 文书ID（可选）
        
        Returns:
            响应数据
        """
        status = callback_data.get('status')
        
        print(f"[OnlyOffice] Callback received, status: {status}, file_id: {file_id}, document_id: {document_id}")
        
        # 状态2或6表示需要保存
        if status in [2, 6]:
            download_url = callback_data.get('url')
            if not download_url:
                return {"error": 1, "message": "Download URL not provided"}
            
            print(f"[OnlyOffice] Document ready to save, download URL: {download_url}")
            
            # 返回成功，实际保存逻辑在API端点中处理
            return {
                "error": 0,
                "message": "Document saved successfully",
                "download_url": download_url
            }
        
        # 其他状态直接返回成功
        return {"error": 0}


# 创建全局实例
onlyoffice_service = OnlyOfficeService()
