import redis.asyncio as redis
from app.core.config import settings
from typing import Optional, Any
import json

class RedisClient:
    def __init__(self):
        self.redis = None
    
    async def connect(self):
        """连接 Redis"""
        try:
            self.redis = await redis.from_url(
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                encoding="utf-8",
                decode_responses=True
            )
            print(f"[Redis] Connected to {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except Exception as e:
            print(f"[Redis] Connection failed: {e}. Continuing without cache...")
            self.redis = None
    
    async def close(self):
        """关闭连接"""
        if self.redis:
            await self.redis.close()
            print("[Redis] Connection closed")
    
    async def get(self, key: str) -> Optional[str]:
        """获取值"""
        if not self.redis:
            return None
        try:
            return await self.redis.get(key)
        except Exception as e:
            print(f"[Redis] Get error: {e}")
            return None
    
    async def set(self, key: str, value: str, expire: int = None):
        """设置值"""
        if not self.redis:
            return
        try:
            await self.redis.set(key, value, ex=expire)
        except Exception as e:
            print(f"[Redis] Set error: {e}")
    
    async def delete(self, key: str):
        """删除键"""
        if not self.redis:
            return
        try:
            await self.redis.delete(key)
        except Exception as e:
            print(f"[Redis] Delete error: {e}")
    
    async def get_json(self, key: str) -> Optional[Any]:
        """获取 JSON 值"""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None
    
    async def set_json(self, key: str, value: Any, expire: int = None):
        """设置 JSON 值"""
        try:
            json_str = json.dumps(value, ensure_ascii=False)
            await self.set(key, json_str, expire)
        except Exception as e:
            print(f"[Redis] Set JSON error: {e}")
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self.redis:
            return False
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            print(f"[Redis] Exists error: {e}")
            return False
    
    async def expire(self, key: str, seconds: int):
        """设置过期时间"""
        if not self.redis:
            return
        try:
            await self.redis.expire(key, seconds)
        except Exception as e:
            print(f"[Redis] Expire error: {e}")
    
    async def ttl(self, key: str) -> int:
        """获取剩余过期时间"""
        if not self.redis:
            return -1
        try:
            return await self.redis.ttl(key)
        except Exception as e:
            print(f"[Redis] TTL error: {e}")
            return -1

redis_client = RedisClient()
