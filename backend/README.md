# 信访智能文书生成系统 - 后端

## 技术栈

- Python 3.12+
- FastAPI
- PostgreSQL
- Redis
- MinIO
- DeepSeek API

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

确保根目录的 `.env` 文件配置正确。

## 数据库管理
    
### 初始化数据库
    
使用脚本初始化表结构：
```bash
python manual_create_tables.py
```
    
### 数据库迁移 (Alembic)
    
本项目使用 Alembic 进行数据库版本管理。
    
**常用命令：**

1. **执行迁移（更新到最新版本）：**
   ```bash
   alembic upgrade head
   ```

2. **创建新迁移脚本（模型变更后）：**
   ```bash
   alembic revision -m "描述变更内容"
   ```
   *生成后需在 `alembic/versions` 编辑脚本内容*
    
3. **回滚到上一个版本：**
   ```bash
   alembic downgrade -1
   ```


## 运行

```bash
python run.py
```

服务将在 http://localhost:8000 启动。

## API 文档

启动后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 主要功能模块

1. **认证模块** (`/api/v1/auth`)
   - 用户注册、登录
   - JWT 令牌认证

2. **文件管理** (`/api/v1/files`)
   - 文件上传、下载、删除
   - 文件预览

3. **文书管理** (`/api/v1/documents`)
   - AI 文档研判
   - AI 文书生成
   - 文书列表查询

4. **模板管理** (`/api/v1/templates`)
   - 模板创建、查询
   - 模板智能提取

5. **版本管理** (`/api/v1/versions`)
   - 版本记录
   - 版本回滚
