import asyncio
import asyncpg

async def test():
    try:
        conn = await asyncpg.connect(
            host='127.0.0.1',
            port=5432,
            user='postgres',
            password='@lzl123456',
            database='petition_system'
        )
        print("✓ 数据库连接成功")
        await conn.close()
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")

asyncio.run(test())
