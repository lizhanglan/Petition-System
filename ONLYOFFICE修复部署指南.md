# ONLYOFFICE修复部署指南

## 问题现状
服务器上的前端代码还是旧版本，显示错误：
```
[OnlyOffice] Editor config: undefined
TypeError: Cannot set properties of undefined (setting 'events')
```

## 已修复的问题
1. ✅ 前端组件：使用 `response.data` 获取配置
2. ✅ 后端下载端点：修复 content_type 和中文文件名编码问题
3. ✅ 本地测试：下载端点工作正常（200 OK）

## 部署步骤

### 方案1：在服务器上重新构建（推荐）

```bash
# 1. SSH到服务器
ssh user@101.37.24.171

# 2. 进入项目目录
cd /path/to/project

# 3. 拉取最新代码
git pull

# 4. 重新构建前端
cd frontend
npm run build

# 5. 重启服务
cd ..
./deploy-server.sh
```

### 方案2：本地构建后上传

```bash
# 1. 本地构建前端
cd frontend
npm run build

# 2. 将 dist 目录上传到服务器
scp -r dist user@101.37.24.171:/path/to/project/frontend/

# 3. SSH到服务器重启服务
ssh user@101.37.24.171
cd /path/to/project
./deploy-server.sh
```

### 方案3：使用部署脚本

如果你的 `deploy-server.sh` 脚本包含前端构建步骤：

```bash
# 1. 推送代码
git add .
git commit -m "修复ONLYOFFICE编辑器加载问题"
git push

# 2. SSH到服务器
ssh user@101.37.24.171

# 3. 拉取并部署
cd /path/to/project
git pull
./deploy-server.sh
```

## 验证步骤

### 1. 检查前端构建
```bash
# 在服务器上
cd /path/to/project/frontend
ls -la dist/  # 确认 dist 目录存在且是最新的
```

### 2. 检查后端日志
```bash
# 查看后端日志
tail -f /path/to/backend/logs/app.log

# 应该看到类似的日志：
# [OnlyOffice] ========== Download Request ==========
# [OnlyOffice] File ID: 5
# [OnlyOffice] SUCCESS: File downloaded from MinIO, size: 189495 bytes
```

### 3. 测试下载端点
```bash
# 在服务器上测试
curl -I http://101.37.24.171:8000/api/v1/onlyoffice/download/file/5

# 应该返回：
# HTTP/1.1 200 OK
# Content-Type: application/pdf
# Content-Length: 189495
```

### 4. 测试前端页面
1. 访问：http://101.37.24.171:8081
2. 登录系统
3. 进入文件管理页面
4. 点击预览按钮
5. 确认编辑器正常加载，不再显示 "Editor config: undefined"

## 关键修复内容

### 前端修复（frontend/src/components/OnlyOfficeEditor.vue）
```javascript
// 修复前（错误）
const config = await request.post('/onlyoffice/config', {...})
config.events = { ... }  // config 是 AxiosResponse，不是配置数据

// 修复后（正确）
const response = await request.post('/onlyoffice/config', {...})
const config = response.data  // 使用 response.data
config.events = { ... }
```

### 后端修复（backend/app/api/v1/endpoints/onlyoffice.py）

**1. MIME类型映射**
```python
mime_types = {
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    # ...
}
content_type = mime_types.get(file.file_type.lower(), 'application/octet-stream')
```

**2. 中文文件名编码**
```python
from urllib.parse import quote
encoded_filename = quote(file.file_name)
"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
```

## 常见问题

### Q1: 前端还是显示旧版本？
**A**: 清除浏览器缓存或使用隐私模式访问

### Q2: 下载端点返回500错误？
**A**: 检查后端日志，确认：
- MinIO连接正常
- 文件存在于数据库
- 文件存在于MinIO

### Q3: 编辑器一直加载？
**A**: 检查：
- ONLYOFFICE服务器是否运行（http://101.37.24.171:9090）
- 后端8000端口是否对ONLYOFFICE服务器开放
- 查看后端日志是否有ONLYOFFICE的下载请求

## 配置检查清单

- [ ] 后端配置正确（backend/.env）
  - ONLYOFFICE_ENABLED=True
  - ONLYOFFICE_SERVER_URL=http://101.37.24.171:9090
  - BACKEND_PUBLIC_URL=http://101.37.24.171:8000
  
- [ ] 前端已重新构建
  - dist 目录存在
  - dist 目录包含最新代码
  
- [ ] 服务已重启
  - 后端服务运行中
  - 前端服务运行中（或Nginx配置正确）
  
- [ ] 网络配置正确
  - 8000端口对ONLYOFFICE服务器开放
  - 9090端口对前端可访问

## 技术支持

如果部署后仍有问题，请提供：
1. 浏览器控制台完整错误信息
2. 后端日志（最近50行）
3. 网络请求详情（F12 -> Network）

---

**修复时间**: 2026-01-03 23:15  
**修复版本**: v1.0.1  
**修复人员**: Kiro AI Assistant
