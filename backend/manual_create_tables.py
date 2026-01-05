"""手动创建数据库表"""
import asyncio
import asyncpg
from app.core.config import settings

# 定义所有表的 SQL
CREATE_TABLES_SQL = """
-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- 文件表
CREATE TABLE IF NOT EXISTS files (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(20) NOT NULL,
    file_size BIGINT NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    file_hash VARCHAR(64),
    status VARCHAR(20) DEFAULT 'uploaded',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_files_user_id ON files(user_id);

-- 模板表（支持 Word 模板）
CREATE TABLE IF NOT EXISTS templates (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    -- Word 模板文件路径（新字段）
    template_file_path VARCHAR(500),
    original_file_path VARCHAR(500),
    -- 字段定义
    fields JSONB,
    -- 兼容旧字段（可为空）
    structure JSONB,
    content_template TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_templates_user_id ON templates(user_id);
CREATE INDEX IF NOT EXISTS idx_templates_document_type ON templates(document_type);

-- 文书表
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    file_id INTEGER REFERENCES files(id),
    template_id INTEGER REFERENCES templates(id),
    title VARCHAR(255) NOT NULL,
    content TEXT,
    structured_content JSONB,
    document_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'draft',
    classification VARCHAR(20) DEFAULT 'public',
    ai_annotations JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);

-- 版本表
CREATE TABLE IF NOT EXISTS versions (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    version_number INTEGER NOT NULL,
    content TEXT,
    structured_content JSONB,
    change_description TEXT,
    diff_data JSONB,
    is_rollback INTEGER DEFAULT 0,
    rollback_from_version INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_versions_document_id ON versions(document_id);

-- 审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    details JSONB,
    ip_address VARCHAR(50),
    user_agent VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
"""

async def create_tables():
    """创建所有数据库表"""
    try:
        # 连接到数据库
        conn = await asyncpg.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB
        )
        
        print("=" * 60)
        print("开始创建数据库表...")
        print("=" * 60)
        
        # 执行 SQL
        await conn.execute(CREATE_TABLES_SQL)
        
        print("✓ 所有表创建成功！")
        print()
        print("已创建的表:")
        print("  - users (用户表)")
        print("  - files (文件表)")
        print("  - templates (模板表)")
        print("  - documents (文书表)")
        print("  - versions (版本表)")
        print("  - audit_logs (审计日志表)")
        print()
        print("=" * 60)
        print("数据库初始化完成！")
        print("=" * 60)
        
        await conn.close()
        return True
    except Exception as e:
        print(f"✗ 创建表失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(create_tables())
