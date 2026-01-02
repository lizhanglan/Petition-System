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
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
