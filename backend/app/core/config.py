from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # 项目信息
    PROJECT_NAME: str = "信访智能文书生成系统"
    VERSION: str = "1.0.0"
    
    # DeepSeek API
    DEEPSEEK_API_KEY: str
    DEEPSEEK_API_BASE: str
    DEEPSEEK_MODEL: str = "deepseek-chat"
    
    # 华为云 Office 预览
    OFFICE_HTTP: str
    OFFICE_API_KEY: str
    OFFICE_APP_SECRET: str
    OFFICE_MCP_APP_CODE: str
    OFFICE_X_APIG_APP_CODE: str
    
    # PostgreSQL
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    
    @property
    def DATABASE_URL(self) -> str:
        # 使用 psycopg（异步）替代 asyncpg
        # 对密码进行 URL 编码以处理特殊字符
        from urllib.parse import quote_plus
        password = quote_plus(self.POSTGRES_PASSWORD)
        return f"postgresql+psycopg://{self.POSTGRES_USER}:{password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    
    # MinIO
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str
    MINIO_SECURE: bool = False
    
    # 后端服务
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    BACKEND_RELOAD: bool = True
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # 文件上传
    MAX_UPLOAD_SIZE: int = 104857600
    ALLOWED_EXTENSIONS: str = "pdf,doc,docx"
    
    @property
    def ALLOWED_EXTENSIONS_LIST(self) -> List[str]:
        return self.ALLOWED_EXTENSIONS.split(",")
    
    # API 调用配置
    API_RETRY_TIMES: int = 3
    API_RETRY_DELAYS: str = "1000,2000,4000"
    API_TIMEOUT: int = 120  # 增加到 120 秒（2 分钟）
    
    @property
    def API_RETRY_DELAYS_LIST(self) -> List[int]:
        return [int(d) for d in self.API_RETRY_DELAYS.split(",")]
    
    # API 限流配置
    RATE_LIMIT_ENABLED: bool = True  # 使用自定义限流实现
    RATE_LIMIT_GLOBAL: str = "100/minute"  # 全局限流：每分钟 100 次
    RATE_LIMIT_USER: str = "50/minute"  # 用户级限流：每分钟 50 次
    RATE_LIMIT_AI: str = "10/minute"  # AI 接口限流：每分钟 10 次
    RATE_LIMIT_UPLOAD: str = "20/minute"  # 上传接口限流：每分钟 20 次
    
    # 降级功能配置
    FALLBACK_ENABLED: bool = True  # 是否启用降级功能
    HEALTH_CHECK_INTERVAL: int = 30  # 健康检查间隔（秒）
    AI_HEALTH_TIMEOUT: int = 5  # AI 健康检查超时时间（秒）
    FAILURE_THRESHOLD: int = 3  # 失败阈值（连续失败次数）
    RECOVERY_THRESHOLD: int = 2  # 恢复阈值（连续成功次数）
    LOCAL_VALIDATION_TIMEOUT: int = 3  # 本地验证超时时间（秒）
    RULES_AUTO_RELOAD: bool = True  # 是否自动重载规则配置
    
    @property
    def RULES_CONFIG_PATH(self) -> str:
        """获取规则配置文件的绝对路径"""
        import os
        from pathlib import Path
        # 获取项目根目录（backend 目录）
        backend_dir = Path(__file__).parent.parent.parent
        config_path = backend_dir / "config" / "validation_rules.json"
        return str(config_path)
    
    # ONLYOFFICE配置（无JWT版本）
    ONLYOFFICE_ENABLED: bool = True
    ONLYOFFICE_SERVER_URL: str = "http://101.37.24.171:9090"
    ONLYOFFICE_JWT_ENABLED: bool = False
    ONLYOFFICE_CALLBACK_URL: str = "http://101.37.24.171:8000/api/v1/onlyoffice/callback"
    BACKEND_PUBLIC_URL: str = "http://101.37.24.171:8000"  # 后端公网地址，用于ONLYOFFICE访问代理端点
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
