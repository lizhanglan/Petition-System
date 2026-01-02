import httpx
from typing import Optional
from app.core.config import settings

class OfficePreviewService:
    """华为云 Office 预览服务"""
    
    def __init__(self):
        self.api_url = settings.OFFICE_HTTP
        self.api_key = settings.OFFICE_API_KEY
        self.app_secret = settings.OFFICE_APP_SECRET
        self.mcp_app_code = settings.OFFICE_MCP_APP_CODE
        self.apig_app_code = settings.OFFICE_X_APIG_APP_CODE
    
    async def get_preview_url(self, file_url: str) -> Optional[str]:
        """获取文件预览 URL"""
        headers = {
            "X-Apig-AppCode": self.apig_app_code,
            "Content-Type": "application/json"
        }
        
        payload = {
            "file_url": file_url,  # 华为云 API 要求使用 file_url 而不是 url
            "app_code": self.mcp_app_code
        }
        
        try:
            print(f"[Preview Service] Requesting preview for URL: {file_url}")
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                )
                
                print(f"[Preview Service] Response status: {response.status_code}")
                print(f"[Preview Service] Response body: {response.text}")
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # 华为云返回的字段是 view_url 而不是 preview_url
                    preview_url = result.get("view_url") or result.get("preview_url")
                    
                    if not preview_url:
                        print(f"[Preview Service] Warning: preview_url is empty in response")
                        return None
                    
                    print(f"[Preview Service] Success: {preview_url}")
                    return preview_url
                else:
                    print(f"[Preview Service] Error: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            print(f"[Preview Service] Exception: {e}")
            import traceback
            traceback.print_exc()
            return None

office_preview_service = OfficePreviewService()
