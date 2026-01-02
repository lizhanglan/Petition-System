import redis.asyncio as redis
from app.core.config import settings

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
        except Exception as e:
            print(f"Redis connection failed: {e}. Continuing without cache...")
            self.redis = None
    
    async def close(self):
        """关闭连接"""
        if self.redis:
            await self.redis.close()
    
    async def get(self, key: str):
        """获取值"""
        if not self.redis:
            return None
        return await self.redis.get(key)
    
    async def set(self, key: str, value: str, expire: int = None):
        """设置值"""
        if not self.redis:
            return
        await self.redis.set(key, value, ex=expire)
    
    async def delete(self, key: str):
        """删除键"""
        if not self.redis:
            return
        await self.redis.delete(key)

redis_client = RedisClient()
