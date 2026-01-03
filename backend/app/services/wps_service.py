"""
WPS开放平台服务
用于文档预览和在线编辑
文档: https://open.wps.cn/docs/
"""
import httpx
import hashlib
import time
import json
from typing import Optional, Dict, Any
from app.core.config import settings


class WPSService:
    """WPS开放平台服务类"""
    
    def __init__(self):
        # WPS开放平台配置
        self.app_id = settings.WPS_APP_ID
        self.app_secret = settings.WPS_APP_SECRET
        self.api_base = settings.WPS_API_BASE or "https://open.wps.cn"
        
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """生成签名"""
        # 按key排序
        sorted_params = sorted(params.items())
        # 拼接字符串
        sign_str = "&".join([f"{k}={v}" for k, v in sorted_params])
        # 添加app_secret
        sign_str = f"{sign_str}&app_secret={self.app_secret}"
        # MD5加密
        return hashlib.md5(sign_str.encode()).hexdigest()
    
    async def get_preview_url(
        self, 
        file_url: str, 
        file_name: str,
        user_id: str,
        permission: str = "read"
    ) -> Optional[str]:
        """
        获取文档预览URL
        
        Args:
            file_url: 文件的公网访问URL
            file_name: 文件名
            user_id: 用户ID
            permission: 权限 (read: 只读, write: 可编辑)
            
        Returns:
            预览URL或None
        """
        try:
            print(f"[WPS] ========== 开始请求WPS预览服务 ==========")
            print(f"[WPS] APP_ID: {self.app_id}")
            print(f"[WPS] API_BASE: {self.api_base}")
            print(f"[WPS] File Name: {file_name}")
            print(f"[WPS] File URL: {file_url}")
            print(f"[WPS] User ID: {user_id}")
            print(f"[WPS] Permission: {permission}")
            
            timestamp = str(int(time.time()))
            
            # 构建请求参数
            params = {
                "app_id": self.app_id,
                "file_url": file_url,
                "file_name": file_name,
                "user_id": user_id,
                "permission": permission,
                "timestamp": timestamp
            }
            
            # 生成签名
            params["signature"] = self._generate_signature(params)
            
            print(f"[WPS] Request params: {json.dumps({k: v for k, v in params.items() if k != 'signature'}, ensure_ascii=False)}")
            print(f"[WPS] Signature: {params['signature'][:20]}...")
            
            # 调用WPS API
            api_url = f"{self.api_base}/api/v1/office/preview"
            print(f"[WPS] API URL: {api_url}")
            
            async with httpx.AsyncClient(timeout=30) as client:
                print(f"[WPS] Sending POST request...")
                response = await client.post(api_url, json=params)
                
                print(f"[WPS] Response status: {response.status_code}")
                print(f"[WPS] Response headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"[WPS] Response body: {json.dumps(result, ensure_ascii=False)}")
                    
                    if result.get("code") == 0:
                        preview_url = result.get("data", {}).get("preview_url")
                        if preview_url:
                            print(f"[WPS] ✓ Success: {preview_url}")
                            return preview_url
                        else:
                            print(f"[WPS] ✗ Error: preview_url is empty in response")
                            return None
                    else:
                        print(f"[WPS] ✗ Error code: {result.get('code')}, message: {result.get('message')}")
                        return None
                else:
                    print(f"[WPS] ✗ HTTP Error: {response.status_code}")
                    print(f"[WPS] Response text: {response.text}")
                    return None
                    
        except httpx.TimeoutException as e:
            print(f"[WPS] ✗ Timeout Exception: {e}")
            return None
        except httpx.RequestError as e:
            print(f"[WPS] ✗ Request Exception: {e}")
            return None
        except Exception as e:
            print(f"[WPS] ✗ Unexpected Exception: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            print(f"[WPS] ========== WPS预览服务请求结束 ==========")

    
    async def get_edit_url(
        self, 
        file_url: str, 
        file_name: str,
        user_id: str,
        user_name: str,
        callback_url: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取文档编辑URL
        
        Args:
            file_url: 文件的公网访问URL
            file_name: 文件名
            user_id: 用户ID
            user_name: 用户名
            callback_url: 保存回调URL
            
        Returns:
            包含edit_url和token的字典，或None
        """
        try:
            timestamp = str(int(time.time()))
            
            # 构建请求参数
            params = {
                "app_id": self.app_id,
                "file_url": file_url,
                "file_name": file_name,
                "user_id": user_id,
                "user_name": user_name,
                "permission": "write",
                "timestamp": timestamp
            }
            
            if callback_url:
                params["callback_url"] = callback_url
            
            # 生成签名
            params["signature"] = self._generate_signature(params)
            
            print(f"[WPS] Requesting edit URL for: {file_name}")
            print(f"[WPS] User: {user_name} (ID: {user_id})")
            
            # 调用WPS API
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.api_base}/api/v1/office/edit",
                    json=params
                )
                
                print(f"[WPS] Response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"[WPS] Response: {json.dumps(result, ensure_ascii=False)}")
                    
                    if result.get("code") == 0:
                        data = result.get("data", {})
                        edit_url = data.get("edit_url")
                        token = data.get("token")
                        
                        print(f"[WPS] Success: {edit_url}")
                        
                        return {
                            "edit_url": edit_url,
                            "token": token,
                            "expires_in": data.get("expires_in", 3600)
                        }
                    else:
                        print(f"[WPS] Error: {result.get('message')}")
                        return None
                else:
                    print(f"[WPS] HTTP Error: {response.status_code}")
                    print(f"[WPS] Response: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"[WPS] Exception: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def handle_save_callback(self, data: Dict[str, Any]) -> bool:
        """
        处理WPS保存回调
        
        Args:
            data: 回调数据
            
        Returns:
            是否处理成功
        """
        try:
            print(f"[WPS] Save callback received: {json.dumps(data, ensure_ascii=False)}")
            
            # 验证签名
            signature = data.pop("signature", None)
            if not signature:
                print("[WPS] No signature in callback")
                return False
            
            expected_signature = self._generate_signature(data)
            if signature != expected_signature:
                print("[WPS] Invalid signature")
                return False
            
            # 获取文件URL
            file_url = data.get("file_url")
            user_id = data.get("user_id")
            
            print(f"[WPS] File saved: {file_url}")
            print(f"[WPS] User: {user_id}")
            
            # TODO: 下载文件并更新到系统
            # 这里需要根据实际业务逻辑处理
            
            return True
            
        except Exception as e:
            print(f"[WPS] Callback error: {e}")
            import traceback
            traceback.print_exc()
            return False


# 创建全局实例
wps_service = WPSService()
