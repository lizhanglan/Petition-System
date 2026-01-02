"""测试各项服务连接"""
import asyncio
from app.core.config import settings
from app.core.minio_client import minio_client
from app.core.redis import redis_client
import asyncpg

async def test_postgres():
    """测试 PostgreSQL 连接"""
    try:
        conn = await asyncpg.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB
        )
        await conn.close()
        print("✓ PostgreSQL 连接成功")
        return True
    except Exception as e:
        print(f"✗ PostgreSQL 连接失败: {e}")
        return False

async def test_redis():
    """测试 Redis 连接"""
    try:
        await redis_client.connect()
        await redis_client.set("test_key", "test_value", expire=10)
        value = await redis_client.get("test_key")
        await redis_client.close()
        if value == "test_value":
            print("✓ Redis 连接成功")
            return True
        else:
            print("✗ Redis 读写测试失败")
            return False
    except Exception as e:
        print(f"✗ Redis 连接失败: {e}")
        return False

def test_minio():
    """测试 MinIO 连接"""
    try:
        # 检查存储桶是否存在
        exists = minio_client.client.bucket_exists(settings.MINIO_BUCKET)
        if exists:
            print("✓ MinIO 连接成功")
            return True
        else:
            print("✗ MinIO 存储桶不存在")
            return False
    except Exception as e:
        print(f"✗ MinIO 连接失败: {e}")
        return False

async def test_deepseek():
    """测试 DeepSeek API"""
    try:
        import httpx
        headers = {
            "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.DEEPSEEK_MODEL,
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 10
        }
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{settings.DEEPSEEK_API_BASE}/chat/completions",
                headers=headers,
                json=payload
            )
            if response.status_code == 200:
                print("✓ DeepSeek API 连接成功")
                return True
            else:
                print(f"✗ DeepSeek API 返回错误: {response.status_code}")
                return False
    except Exception as e:
        print(f"✗ DeepSeek API 连接失败: {e}")
        return False

async def main():
    print("=" * 50)
    print("开始测试服务连接...")
    print("=" * 50)
    
    results = []
    
    # 测试 PostgreSQL
    results.append(await test_postgres())
    
    # 测试 Redis
    results.append(await test_redis())
    
    # 测试 MinIO
    results.append(test_minio())
    
    # 测试 DeepSeek API
    results.append(await test_deepseek())
    
    print("=" * 50)
    if all(results):
        print("所有服务连接正常！")
    else:
        print("部分服务连接失败，请检查配置")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
