"""
预览服务选择器
根据配置优先使用ONLYOFFICE服务，失败时降级到华为云服务
"""
from typing import Optional, Dict, Any
from app.core.config import settings
from app.services.onlyoffice_service import onlyoffice_service
from app.services.office_preview_service import office_preview_service


class PreviewServiceSelector:
    """预览服务选择器，实现ONLYOFFICE优先，华为云降级的策略"""
    
    async def get_preview_url(
        self,
        file_url: str,
        file_name: str,
        user_id: str,
        permission: str = "read"
    ) -> Optional[Dict[str, Any]]:
        """
        获取文档预览URL（优先使用ONLYOFFICE，失败时降级到华为云）
        
        Args:
            file_url: 文件的公网访问URL
            file_name: 文件名
            user_id: 用户ID
            permission: 权限 (read: 只读, write: 可编辑)
            
        Returns:
            包含preview_url和service_type的字典，或None
        """
        preview_url = None
        service_type = None
        
        # 1. 优先尝试ONLYOFFICE服务（如果已启用）
        if settings.ONLYOFFICE_ENABLED and settings.ONLYOFFICE_SERVER_URL:
            print(f"[PreviewSelector] 尝试使用ONLYOFFICE服务...")
            try:
                # ONLYOFFICE使用前端组件，返回特殊标记
                service_type = "onlyoffice"
                print(f"[PreviewSelector] ONLYOFFICE服务可用")
                return {
                    "preview_url": "use_onlyoffice_component",  # 前端识别此标记使用ONLYOFFICE组件
                    "service_type": service_type,
                    "file_url": file_url
                }
            except Exception as e:
                print(f"[PreviewSelector] ONLYOFFICE服务异常: {e}，尝试降级...")
        else:
            print(f"[PreviewSelector] ONLYOFFICE服务未启用（ONLYOFFICE_ENABLED={settings.ONLYOFFICE_ENABLED}）")
        
        # 2. 降级到华为云服务
        print(f"[PreviewSelector] 使用华为云预览服务...")
        try:
            preview_url = await office_preview_service.get_preview_url(file_url)
            
            if preview_url:
                service_type = "huawei"
                print(f"[PreviewSelector] 华为云服务成功: {preview_url}")
                return {
                    "preview_url": preview_url,
                    "service_type": service_type,
                    "file_url": file_url
                }
            else:
                print(f"[PreviewSelector] 华为云服务返回空URL")
        except Exception as e:
            print(f"[PreviewSelector] 华为云服务异常: {e}")
        
        # 3. 所有服务都失败
        print(f"[PreviewSelector] 所有预览服务都失败，返回直接URL")
        
        # 对于PDF文件，可以直接在浏览器中预览
        if file_name.lower().endswith('.pdf'):
            return {
                "preview_url": file_url,
                "service_type": "direct",
                "file_url": file_url
            }
        
        # 其他格式不支持预览
        return {
            "preview_url": None,
            "service_type": "unsupported",
            "file_url": file_url
        }
    
    async def get_edit_url(
        self,
        file_url: str,
        file_name: str,
        user_id: str,
        user_name: str,
        callback_url: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取文档编辑URL（优先使用ONLYOFFICE）
        
        Args:
            file_url: 文件的公网访问URL
            file_name: 文件名
            user_id: 用户ID
            user_name: 用户名
            callback_url: 保存回调URL
            
        Returns:
            包含edit_url、token等信息的字典，或None
        """
        # 1. 优先使用ONLYOFFICE编辑功能
        if settings.ONLYOFFICE_ENABLED and settings.ONLYOFFICE_SERVER_URL:
            print(f"[PreviewSelector] 使用ONLYOFFICE编辑服务...")
            try:
                # ONLYOFFICE使用前端组件，返回特殊标记
                print(f"[PreviewSelector] ONLYOFFICE编辑服务可用")
                return {
                    "edit_url": "use_onlyoffice_component",  # 前端识别此标记使用ONLYOFFICE组件
                    "service_type": "onlyoffice",
                    "file_url": file_url
                }
            except Exception as e:
                print(f"[PreviewSelector] ONLYOFFICE编辑服务异常: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[PreviewSelector] ONLYOFFICE服务未启用，无法提供编辑功能")
        
        # 2. 编辑功能不支持降级（华为云仅支持预览）
        return None


# 创建全局实例
preview_service_selector = PreviewServiceSelector()
