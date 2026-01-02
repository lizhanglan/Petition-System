"""创建数据库"""
import asyncio
import asyncpg
from app.core.config import settings

async def create_database():
    """创建数据库"""
    try:
        # 连接到默认的 postgres 数据库
        conn = await asyncpg.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database='postgres'
        )
        
        # 检查数据库是否存在
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            settings.POSTGRES_DB
        )
        
        if not exists:
            # 创建数据库
            await conn.execute(f'CREATE DATABASE {settings.POSTGRES_DB}')
            print(f"✓ 数据库 '{settings.POSTGRES_DB}' 创建成功")
        else:
            print(f"✓ 数据库 '{settings.POSTGRES_DB}' 已存在")
        
        await conn.close()
        return True
    except Exception as e:
        print(f"✗ 创建数据库失败: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(create_database())
