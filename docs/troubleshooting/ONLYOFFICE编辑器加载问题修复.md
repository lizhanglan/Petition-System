# ONLYOFFICE编辑器加载问题修复

## 问题描述
ONLYOFFICE编辑器一直显示"正在加载编辑器..."，`onDocumentReady`事件未触发，无法显示文档内容。

## 根本原因
发现了两个关键问题：

### 1. 前端组件错误
**问题**：前端组件直接使用Axios响应对象作为配置，而不是响应数据。

**位置**：`frontend/src/components/OnlyOfficeEditor.vue`

**错误代码**：
```javascript
const config = await request.post('/onlyoffice/config', {...})
config.events = { ... }  // 错误：config是AxiosResponse对象，不是配置数据
```

**修复**：
```javascript
const response = await request.post('/onlyoffice/config', {...})
const config = response.data  // 正确：使用response.data获取配置数据
config.events = { ... }
```

### 2. 后端下载端点错误
**问题1**：使用了不存在的`content_type`字段

File模型只有`file_type`字段，没有`content_type`字段。

**修复**：添加MIME类型映射
```python
mime_types = {
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'xls': 'application/vnd.ms-excel',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'ppt': 'application/vnd.ms-powerpoint',
    'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
}
content_type = mime_types.get(file.file_type.lower(), 'application/octet-stream')
```

**问题2**：中文文件名编码错误

HTTP头部使用latin-1编码，无法处理中文字符。

**错误**：
```python
"Content-Disposition": f'attachment; filename="{file.file_name}"'
# 错误：'latin-1' codec can't encode characters
```

**修复**：使用RFC 5987标准的UTF-8编码
```python
from urllib.parse import quote
encoded_filename = quote(file.file_name)
"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
```

## 修复的文件

### 1. frontend/src/components/OnlyOfficeEditor.vue
- 修复：使用`response.data`获取配置数据

### 2. backend/app/api/v1/endpoints/onlyoffice.py
- 修复：添加MIME类型映射（替代不存在的content_type字段）
- 修复：使用UTF-8编码处理中文文件名
- 增强：添加详细的调试日志
- 增强：添加CORS头部支持

## 测试结果

### 下载端点测试
```powershell
# 测试文件ID 5
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/onlyoffice/download/file/5"
# ✓ 成功! 状态码: 200, 大小: 189495 bytes
```

### 后端日志
```
[OnlyOffice] ========== Download Request ==========
[OnlyOffice] File ID: 5
[OnlyOffice] Client IP: 127.0.0.1
[OnlyOffice] File found: 广西警察学院关于给予董光辉同学留校察看处分的决定.pdf
[OnlyOffice] Storage path: uploads/2/20260103010912_...
[OnlyOffice] File type: pdf
[OnlyOffice] Content type: application/pdf
[OnlyOffice] Downloading from MinIO...
[OnlyOffice] SUCCESS: File downloaded from MinIO, size: 189495 bytes
INFO: 127.0.0.1:59941 - "GET /api/v1/onlyoffice/download/file/5 HTTP/1.1" 200 OK
```

## 下一步操作

### 1. 推送代码到服务器
```bash
git add .
git commit -m "修复ONLYOFFICE编辑器加载问题"
git push
```

### 2. 在服务器上部署
```bash
# SSH到服务器
ssh user@101.37.24.171

# 拉取最新代码
cd /path/to/project
git pull

# 重启服务
./deploy-server.sh
```

### 3. 验证功能
1. 访问文件管理页面
2. 点击预览按钮
3. 确认ONLYOFFICE编辑器正常加载
4. 确认文档内容正常显示

## 关键配置

### 后端配置（backend/.env）
```env
ONLYOFFICE_ENABLED=True
ONLYOFFICE_SERVER_URL=http://101.37.24.171:9090
ONLYOFFICE_JWT_ENABLED=False
ONLYOFFICE_CALLBACK_URL=http://101.37.24.171:8000/api/v1/onlyoffice/callback
BACKEND_PUBLIC_URL=http://101.37.24.171:8000
```

### 前端配置
ONLYOFFICE API脚本：`http://101.37.24.171:9090/web-apps/apps/api/documents/api.js`

## 技术要点

### 1. 后端代理方案
ONLYOFFICE服务器无法直接访问外部URL（如MinIO），因此使用后端代理：
```
ONLYOFFICE → 后端代理端点 → MinIO
```

### 2. 无认证端点
下载代理端点不需要认证，因为ONLYOFFICE服务器无法提供用户token。

### 3. 中文文件名处理
使用RFC 5987标准的`filename*=UTF-8''`格式处理中文文件名。

### 4. CORS支持
添加CORS头部允许ONLYOFFICE服务器跨域访问。

## 修复时间
2026-01-03 23:15

## 修复人员
Kiro AI Assistant
