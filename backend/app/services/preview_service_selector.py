"""
预览服务选择器
根据配置优先使用WPS服务，失败时降级到华为云服务
"""
from typing import Optional, Dict, Any
from app.core.config import settings
from app.services.wps_service import wps_service
from app.services.office_preview_service import office_preview_service


class PreviewServiceSelector:
    """预览服务选择器，实现WPS优先，华为云降级的策略"""
    
    async def get_preview_url(
        self,
        file_url: str,
        file_name: str,
        user_id: str,
        permission: str = "read"
    ) -> Optional[Dict[str, Any]]:
        """
        获取文档预览URL（优先使用WPS，失败时降级到华为云）
        
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
        
        # 1. 优先尝试WPS服务（如果已启用）
        if settings.WPS_ENABLED and settings.WPS_APP_ID and settings.WPS_APP_SECRET:
            print(f"[PreviewSelector] 尝试使用WPS服务...")
            try:
                preview_url = await wps_service.get_preview_url(
                    file_url=file_url,
                    file_name=file_name,
                    user_id=user_id,
                    permission=permission
                )
                
                if preview_url:
                    service_type = "wps"
                    print(f"[PreviewSelector] WPS服务成功: {preview_url}")
                    return {
                        "preview_url": preview_url,
                        "service_type": service_type,
                        "file_url": file_url
                    }
                else:
                    print(f"[PreviewSelector] WPS服务返回空URL，尝试降级...")
            except Exception as e:
                print(f"[PreviewSelector] WPS服务异常: {e}，尝试降级...")
        else:
            print(f"[PreviewSelector] WPS服务未启用（WPS_ENABLED={settings.WPS_ENABLED}）")
        
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
        获取文档编辑URL（仅支持WPS）
        
        Args:
            file_url: 文件的公网访问URL
            file_name: 文件名
            user_id: 用户ID
            user_name: 用户名
            callback_url: 保存回调URL
            
        Returns:
            包含edit_url、token等信息的字典，或None
        """
        # 编辑功能仅支持WPS
        if not settings.WPS_ENABLED or not settings.WPS_APP_ID or not settings.WPS_APP_SECRET:
            print(f"[PreviewSelector] WPS服务未启用，无法提供编辑功能")
            return None
        
        print(f"[PreviewSelector] 使用WPS编辑服务...")
        try:
            result = await wps_service.get_edit_url(
                file_url=file_url,
                file_name=file_name,
                user_id=user_id,
                user_name=user_name,
                callback_url=callback_url
            )
            
            if result:
                result["service_type"] = "wps"
                print(f"[PreviewSelector] WPS编辑服务成功")
            else:
                print(f"[PreviewSelector] WPS编辑服务失败")
            
            return result
        except Exception as e:
            print(f"[PreviewSelector] WPS编辑服务异常: {e}")
            import traceback
            traceback.print_exc()
            return None


# 创建全局实例
preview_service_selector = PreviewServiceSelector()
