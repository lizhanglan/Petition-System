from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# 创建异步引擎（使用 psycopg）
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# 创建会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# 声明基类
Base = declarative_base()

async def get_db():
    """数据库会话依赖"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """初始化数据库表"""
    try:
        async with engine.begin() as conn:
            # 导入所有模型以确保它们被注册
            from app.models import user, file, document, template, version, audit_log
            await conn.run_sync(Base.metadata.create_all)
        print("✓ 数据库表初始化成功")
    except Exception as e:
        print(f"✗ 数据库表初始化失败: {e}")
        # 不抛出异常，允许应用继续启动
        pass
