"""
审计日志辅助函数
"""

from fastapi import Request
from typing import Optional


def get_client_ip(request: Request) -> Optional[str]:
    """
    获取客户端 IP 地址
    
    优先级：
    1. X-Forwarded-For (代理/负载均衡)
    2. X-Real-IP (Nginx)
    3. request.client.host (直连)
    """
    # 检查代理头
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For 可能包含多个 IP，取第一个
        return forwarded.split(",")[0].strip()
    
    # 检查 Nginx 代理头
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 直连 IP
    if request.client:
        return request.client.host
    
    return None


def get_user_agent(request: Request) -> Optional[str]:
    """获取 User Agent"""
    return request.headers.get("User-Agent")
