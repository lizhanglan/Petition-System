from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import init_db
from app.api.v1 import api_router
from app.services.health_monitor_service import init_health_monitor
from app.services.local_rules_engine import init_local_rules_engine
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时不初始化数据库（表已手动创建）
    print("✓ 应用启动，跳过数据库初始化")
    if settings.RATE_LIMIT_ENABLED:
        print(f"✓ API 限流已启用")
        print(f"  - 全局限流: {settings.RATE_LIMIT_GLOBAL}")
        print(f"  - 用户限流: {settings.RATE_LIMIT_USER}")
        print(f"  - AI 接口: {settings.RATE_LIMIT_AI}")
        print(f"  - 上传接口: {settings.RATE_LIMIT_UPLOAD}")
    
    # 初始化降级功能
    if settings.FALLBACK_ENABLED:
        print(f"✓ 降级功能已启用")
        
        # 初始化本地规则引擎
        try:
            local_engine = init_local_rules_engine(settings.RULES_CONFIG_PATH)
            
            # 加载规则配置
            config = await local_engine.config_manager.load_config()
            if config:
                print(f"  - 规则配置已加载: {len(config.rules)} 个规则")
                
                # 启动配置文件监控
                if settings.RULES_AUTO_RELOAD:
                    await local_engine.config_manager.start_watching()
                    print(f"  - 配置文件自动重载已启用")
            else:
                print(f"  ⚠ 规则配置加载失败，降级功能可能不可用")
        except Exception as e:
            print(f"  ⚠ 本地规则引擎初始化失败: {e}")
        
        # 初始化健康监控服务
        try:
            health_monitor = init_health_monitor(
                check_interval=settings.HEALTH_CHECK_INTERVAL,
                failure_threshold=settings.FAILURE_THRESHOLD,
                recovery_threshold=settings.RECOVERY_THRESHOLD,
                timeout=settings.AI_HEALTH_TIMEOUT
            )
            
            # 启动健康监控
            await health_monitor.start_monitoring()
            print(f"  - 健康监控已启动（间隔: {settings.HEALTH_CHECK_INTERVAL}秒）")
            print(f"  - 失败阈值: {settings.FAILURE_THRESHOLD} 次")
            print(f"  - 恢复阈值: {settings.RECOVERY_THRESHOLD} 次")
        except Exception as e:
            print(f"  ⚠ 健康监控服务初始化失败: {e}")
    
    yield
    
    # 关闭时清理资源
    if settings.FALLBACK_ENABLED:
        try:
            from app.services.health_monitor_service import get_health_monitor
            from app.services.local_rules_engine import get_local_rules_engine
            
            health_monitor = get_health_monitor()
            if health_monitor:
                await health_monitor.stop_monitoring()
                print("✓ 健康监控服务已停止")
            
            local_engine = get_local_rules_engine()
            if local_engine and settings.RULES_AUTO_RELOAD:
                local_engine.config_manager.stop_watching()
                print("✓ 配置文件监控已停止")
        except Exception as e:
            print(f"⚠ 清理资源时出错: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
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


