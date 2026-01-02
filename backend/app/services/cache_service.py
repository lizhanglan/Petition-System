"""
缓存服务
提供统一的缓存接口和策略
"""
from typing import Optional, Any, Callable
from functools import wraps
import hashlib
import json
from app.core.redis import redis_client

class CacheService:
    """缓存服务"""
    
    # 缓存过期时间（秒）
    CACHE_TTL = {
        "template_list": 300,      # 模板列表：5分钟
        "document_list": 60,        # 文档列表：1分钟
        "file_list": 60,            # 文件列表：1分钟
        "user_info": 600,           # 用户信息：10分钟
        "audit_stats": 300,         # 审计统计：5分钟
        "classifications": 3600,    # 密级选项：1小时
    }
    
    @staticmethod
    def generate_key(prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        # 将参数转换为字符串
        params = f"{args}_{kwargs}"
        # 生成哈希值
        hash_value = hashlib.md5(params.encode()).hexdigest()[:8]
        return f"{prefix}:{hash_value}"
    
    @staticmethod
    async def get(key: str) -> Optional[Any]:
        """获取缓存"""
        return await redis_client.get_json(key)
    
    @staticmethod
    async def set(key: str, value: Any, ttl: int = 300):
        """设置缓存"""
        await redis_client.set_json(key, value, expire=ttl)
    
    @staticmethod
    async def delete(key: str):
        """删除缓存"""
        await redis_client.delete(key)
    
    @staticmethod
    async def clear_pattern(pattern: str):
        """清除匹配模式的缓存（需要 Redis 支持）"""
        # 注意：这需要 Redis SCAN 命令支持
        # 简化实现，实际生产环境需要更复杂的逻辑
        pass

def cache_result(prefix: str, ttl: int = 300):
    """
    缓存装饰器
    
    使用示例：
    @cache_result("template_list", ttl=300)
    async def get_template_list(user_id: int):
        ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = CacheService.generate_key(prefix, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_value = await CacheService.get(cache_key)
            if cached_value is not None:
                print(f"[Cache] Hit: {cache_key}")
                return cached_value
            
            # 缓存未命中，执行函数
            print(f"[Cache] Miss: {cache_key}")
            result = await func(*args, **kwargs)
            
            # 存入缓存
            if result is not None:
                await CacheService.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

cache_service = CacheService()
