import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.BACKEND_RELOAD,
        timeout_keep_alive=300,  # 保持连接超时：5分钟
        limit_max_requests=10000,  # 最大请求数
        limit_concurrency=1000  # 最大并发连接数
    )
