import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

async def test():
    try:
        engine = create_async_engine(
            "postgresql+asyncpg://postgres:@lzl123456@127.0.0.1:5432/petition_system",
            echo=False
        )
        async with engine.begin() as conn:
            result = await conn.execute("SELECT 1")
            print("✓ SQLAlchemy 连接成功")
        await engine.dispose()
    except Exception as e:
        print(f"✗ SQLAlchemy 连接失败: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test())
