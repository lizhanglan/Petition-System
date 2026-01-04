# ONLYOFFICE HEAD请求修复完成

## 问题描述

ONLYOFFICE编辑器一直显示"正在加载编辑器..."，`onDocumentReady`事件未触发。

## 根本原因

ONLYOFFICE服务器在下载文件前会发送HEAD请求检查文件是否存在，但后端下载端点只支持GET方法，导致返回405 Method Not Allowed。

## 解决方案

### 1. 添加HEAD方法支持

修改 `backend/app/api/v1/endpoints/onlyoffice.py`：

```python
# 修改前
@router.get("/download/file/{file_id}")

# 修改后
@router.api_route("/download/file/{file_id}", methods=["GET", "HEAD"])
```

### 2. 添加HEAD请求处理逻辑

```python
# 对文件名进行URL编码以支持中文
from urllib.parse import quote
encoded_filename = quote(file.file_name)

# 如果是HEAD请求，只返回头部信息
if request.method == "HEAD":
    print(f"[OnlyOffice] HEAD request - returning headers only")
    return StreamingResponse(
        io.BytesIO(b""),
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )
```

### 3. 启用后端热更新

修改 `docker-compose.yml`，添加代码目录挂载：

```yaml
backend:
  volumes:
    - ./backend/app:/app/app  # 挂载代码目录，支持热更新
    - ./backend/logs:/app/logs
    - ./backend/uploads:/app/uploads
    - ./backend/config:/app/config
```

## 部署步骤

### 服务器上执行：

```bash
# 1. 进入项目目录
cd ~/lizhanglan/Petition-System

# 2. 拉取最新代码
git pull origin main

# 3. 重新创建后端容器（应用新的挂载配置）
docker-compose stop backend && docker-compose rm -f backend
docker-compose up -d backend

# 4. 等待容器启动
sleep 15

# 5. 测试HEAD请求
curl -I http://101.37.24.171:8000/api/v1/onlyoffice/download/file/1
```

## 验证结果

```bash
HTTP/1.1 200 OK
date: Sun, 04 Jan 2026 08:26:15 GMT
server: uvicorn
content-disposition: attachment; filename*=UTF-8''20260102152715_...docx
access-control-allow-origin: *
access-control-allow-methods: GET, HEAD, OPTIONS
access-control-allow-headers: *
content-type: application/vnd.openxmlformats-officedocument.wordprocessingml.document
```

✅ HEAD请求返回200 OK
✅ 包含正确的响应头
✅ CORS配置正确

## 后续维护

### 修改后端代码后的部署流程：

1. **本地修改代码**
2. **推送到GitHub**：`git push origin main`
3. **服务器上更新**：
   ```bash
   cd ~/lizhanglan/Petition-System
   git pull origin main
   docker-compose restart backend
   ```

**注意**：由于启用了代码挂载，Python代码修改后只需重启容器，不需要重新构建镜像。

### 修改前端代码后的部署流程：

前端使用多阶段构建，不支持热更新，需要重新构建镜像：

```bash
cd ~/lizhanglan/Petition-System
git pull origin main
docker-compose stop frontend && docker-compose rm -f frontend
docker-compose build frontend --no-cache
docker-compose up -d frontend
```

## 相关文件

- `backend/app/api/v1/endpoints/onlyoffice.py` - 后端API端点
- `docker-compose.yml` - Docker配置
- `frontend/src/components/OnlyOfficeEditor.vue` - 前端编辑器组件

## 提交记录

- `574dc2a` - 修复ONLYOFFICE下载端点：添加HEAD方法支持
- `ef42052` - 添加后端代码目录挂载，支持热更新
- `c97f757` - 修复HEAD请求处理：在使用前定义encoded_filename变量

## 状态

✅ **已完成** - 2026-01-04

HEAD请求已正常工作，等待前端测试ONLYOFFICE编辑器加载。
