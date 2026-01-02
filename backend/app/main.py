from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import init_db
from app.api.v1 import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时不初始化数据库（表已手动创建）
    print("✓ 应用启动，跳过数据库初始化")
    yield
    # 关闭时清理资源

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "信访智能文书生成系统 API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
