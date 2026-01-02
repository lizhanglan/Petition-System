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

## 初始化数据库

系统启动时会自动创建数据库表。

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
