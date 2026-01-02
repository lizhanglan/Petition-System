"""
API 限流中间件
简单的内存限流实现（避免 slowapi 的编码问题）
"""
from fastapi import Request, HTTPException
from functools import wraps
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple
import asyncio

from app.core.config import settings

class SimpleRateLimiter:
    """简单的内存限流器"""
    
    def __init__(self):
        # 存储格式: {key: [(timestamp, count)]}
        self.requests: Dict[str, list] = defaultdict(list)
        self.enabled = settings.RATE_LIMIT_ENABLED
        self.lock = asyncio.Lock()
    
    def _parse_limit(self, limit_str: str) -> Tuple[int, int]:
        """解析限流字符串，如 '10/minute' -> (10, 60)"""
        parts = limit_str.split('/')
        count = int(parts[0])
        
        unit = parts[1] if len(parts) > 1 else 'minute'
        seconds_map = {
            'second': 1,
            'minute': 60,
            'hour': 3600,
            'day': 86400
        }
        seconds = seconds_map.get(unit, 60)
        
        return count, seconds
    
    async def check_limit(self, key: str, limit_str: str) -> bool:
        """检查是否超过限流"""
        if not self.enabled:
            return True
        
        max_requests, window_seconds = self._parse_limit(limit_str)
        now = datetime.now()
        window_start = now - timedelta(seconds=window_seconds)
        
        async with self.lock:
            # 清理过期记录
            self.requests[key] = [
                ts for ts in self.requests[key]
                if ts > window_start
            ]
            
            # 检查是否超限
            if len(self.requests[key]) >= max_requests:
                return False
            
            # 记录本次请求
            self.requests[key].append(now)
            return True
    
    def get_user_identifier(self, request: Request) -> str:
        """获取用户标识符"""
        # 尝试从请求状态中获取用户信息
        user = getattr(request.state, "user", None)
        if user and hasattr(user, "id"):
            return f"user:{user.id}"
        
        # 回退到 IP 地址
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"

# 全局限流器实例
rate_limiter = SimpleRateLimiter()

print(f"[RateLimiter] Initialized simple rate limiter")
print(f"[RateLimiter] Enabled: {settings.RATE_LIMIT_ENABLED}")

# 限流装饰器
def rate_limit(limit_str: str):
    """
    限流装饰器
    
    使用示例：
    @rate_limit("10/minute")
    async def my_endpoint(request: Request):
        pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从参数中找到 Request 对象
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                request = kwargs.get('req') or kwargs.get('request')
            
            if request and rate_limiter.enabled:
                key = rate_limiter.get_user_identifier(request)
                if not await rate_limiter.check_limit(key, limit_str):
                    raise HTTPException(
                        status_code=429,
                        detail=f"Rate limit exceeded: {limit_str}"
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 预定义的限流装饰器
def user_rate_limit(func):
    return rate_limit(settings.RATE_LIMIT_USER)(func)

def ai_rate_limit(func):
    return rate_limit(settings.RATE_LIMIT_AI)(func)

def upload_rate_limit(func):
    return rate_limit(settings.RATE_LIMIT_UPLOAD)(func)

# 为了兼容性，创建一个 limiter 对象
class LimiterCompat:
    """兼容 slowapi 的 limiter 对象"""
    pass

limiter = LimiterCompat()
