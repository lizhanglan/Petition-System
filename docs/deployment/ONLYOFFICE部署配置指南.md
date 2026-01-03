# ONLYOFFICE部署配置指南

## 概述

本指南帮助您完成ONLYOFFICE集成的部署和配置工作。

## 前置条件

### 必需条件
- ✅ ONLYOFFICE服务器已部署：`http://101.37.24.171:9090`
- ✅ ONLYOFFICE JWT验证已关闭
- ⚠️ **后端必须有公网IP或域名**（ONLYOFFICE需要访问）
- ✅ MinIO存储服务正常运行
- ✅ PostgreSQL数据库正常运行

### 网络要求
```
前端浏览器 → ONLYOFFICE服务器（101.37.24.171:9090）✅
ONLYOFFICE服务器 → 后端公网IP（需要配置）⚠️
后端 → MinIO存储 ✅
```

## 部署步骤

### 步骤1：配置后端环境变量

编辑 `backend/.env` 文件：

```bash
# ONLYOFFICE配置（无JWT版本）
ONLYOFFICE_ENABLED=true
ONLYOFFICE_SERVER_URL=http://101.37.24.171:9090
ONLYOFFICE_JWT_ENABLED=false

# ⚠️ 重要：必须配置后端的公网地址
# 将 your-backend-public-ip 替换为实际的公网IP或域名
ONLYOFFICE_CALLBACK_URL=http://your-backend-public-ip:8000/api/v1/onlyoffice/callback
BACKEND_PUBLIC_URL=http://your-backend-public-ip:8000
```

**配置示例**：

如果后端公网IP是 `123.45.67.89`：
```bash
ONLYOFFICE_CALLBACK_URL=http://123.45.67.89:8000/api/v1/onlyoffice/callback
BACKEND_PUBLIC_URL=http://123.45.67.89:8000
```

如果使用域名 `api.example.com`：
```bash
ONLYOFFICE_CALLBACK_URL=https://api.example.com/api/v1/onlyoffice/callback
BACKEND_PUBLIC_URL=https://api.example.com
```

### 步骤2：配置防火墙规则

确保以下端口可访问：

#### 后端服务器
```bash
# 允许ONLYOFFICE服务器访问后端
# 如果使用云服务器，在安全组中添加规则：
# 来源：101.37.24.171
# 端口：8000
# 协议：TCP
```

#### 前端访问
```bash
# 允许用户浏览器访问ONLYOFFICE
# 端口：9090（ONLYOFFICE服务器）
# 协议：TCP
```

### 步骤3：验证配置

#### 3.1 检查后端健康状态

```bash
curl http://localhost:8000/api/v1/onlyoffice/health
```

预期响应：
```json
{
  "status": "ok",
  "onlyoffice_enabled": false,
  "server_url": "http://101.37.24.171:9090",
  "backend_public_url": "http://your-backend-public-ip:8000"
}
```

#### 3.2 测试代理端点（从ONLYOFFICE服务器）

在ONLYOFFICE服务器上执行：
```bash
curl http://your-backend-public-ip:8000/api/v1/onlyoffice/download/file/1
```

如果返回文件内容或404（文件不存在），说明代理端点可访问。

#### 3.3 使用测试页面验证

1. 打开 `test_onlyoffice_with_backend.html`
2. 配置后端地址
3. 点击"测试后端连接"
4. 点击"测试代理端点"
5. 点击"预览模式"或"编辑模式"

### 步骤4：重启服务

```bash
# 重启后端服务
cd backend
python run.py

# 或使用Docker
docker-compose restart backend
```

### 步骤5：前端集成（可选）

如果需要在前端页面中使用ONLYOFFICE编辑器：

```vue
<template>
  <OnlyOfficeEditor
    :file-id="fileId"
    mode="edit"
    @error="handleError"
  />
</template>

<script setup>
import OnlyOfficeEditor from '@/components/OnlyOfficeEditor.vue'

const fileId = ref(1)

const handleError = (error) => {
  console.error('Editor error:', error)
}
</script>
```

## 配置检查清单

### 必需配置
- [ ] `ONLYOFFICE_ENABLED=true`
- [ ] `ONLYOFFICE_SERVER_URL=http://101.37.24.171:9090`
- [ ] `ONLYOFFICE_JWT_ENABLED=false`
- [ ] `ONLYOFFICE_CALLBACK_URL` 配置为后端公网地址
- [ ] `BACKEND_PUBLIC_URL` 配置为后端公网地址

### 网络配置
- [ ] 后端有公网IP或域名
- [ ] ONLYOFFICE可以访问后端公网IP
- [ ] 防火墙允许ONLYOFFICE访问后端端口8000
- [ ] 用户浏览器可以访问ONLYOFFICE服务器端口9090

### 服务验证
- [ ] ONLYOFFICE服务正常运行
- [ ] 后端健康检查通过
- [ ] 代理端点可访问
- [ ] 测试页面加载成功

## 常见问题

### Q1: 如何获取后端公网IP？

**云服务器**：
```bash
# 阿里云/腾讯云/华为云
# 在控制台查看实例的公网IP
```

**本地开发**：
```bash
# 使用内网穿透工具（如ngrok）
ngrok http 8000

# 使用返回的公网URL配置BACKEND_PUBLIC_URL
```

### Q2: 后端没有公网IP怎么办？

**方案1：使用内网穿透**
```bash
# 安装ngrok
# 运行：ngrok http 8000
# 使用ngrok提供的URL配置BACKEND_PUBLIC_URL
```

**方案2：配置端口转发**
```bash
# 在路由器或防火墙配置端口转发
# 外部端口 → 内部IP:8000
```

**方案3：使用反向代理**
```bash
# 使用Nginx或Caddy配置反向代理
# 将公网域名代理到内部后端服务
```

### Q3: 编辑器显示"下载失败"（错误代码-4）

**原因**：ONLYOFFICE无法访问后端代理URL

**排查步骤**：
1. 检查 `BACKEND_PUBLIC_URL` 配置是否正确
2. 在ONLYOFFICE服务器上测试：
   ```bash
   curl http://your-backend-public-ip:8000/api/v1/onlyoffice/health
   ```
3. 检查防火墙规则
4. 查看后端日志确认是否收到请求

### Q4: 保存回调失败

**原因**：ONLYOFFICE无法访问回调URL

**解决方案**：
1. 检查 `ONLYOFFICE_CALLBACK_URL` 配置
2. 确保使用公网IP而非localhost
3. 在ONLYOFFICE服务器上测试：
   ```bash
   curl -X POST http://your-backend-public-ip:8000/api/v1/onlyoffice/callback
   ```
4. 查看后端日志

### Q5: 如何启用HTTPS？

**步骤**：
1. 配置SSL证书
2. 更新配置使用HTTPS：
   ```bash
   ONLYOFFICE_CALLBACK_URL=https://api.example.com/api/v1/onlyoffice/callback
   BACKEND_PUBLIC_URL=https://api.example.com
   ```
3. 确保ONLYOFFICE服务器也使用HTTPS

## 性能优化

### 1. 使用CDN加速

将ONLYOFFICE静态资源配置到CDN：
```javascript
// 修改API脚本URL
script.src = 'https://cdn.example.com/onlyoffice/api.js'
```

### 2. 启用缓存

在后端添加Redis缓存：
```python
# 缓存编辑器配置
cache_key = f"onlyoffice_config_{file_id}"
config = await redis.get(cache_key)
if not config:
    config = await generate_config()
    await redis.set(cache_key, config, expire=3600)
```

### 3. 优化文件传输

```python
# 使用流式传输
return StreamingResponse(
    file_stream,
    media_type=content_type,
    headers={"Content-Length": str(file_size)}
)
```

## 监控和日志

### 查看后端日志

```bash
# 查看ONLYOFFICE相关日志
tail -f backend/logs/app.log | grep OnlyOffice
```

### 监控指标

- 编辑器加载时间
- 文件下载速度
- 保存成功率
- 错误率

### 告警配置

```python
# 配置告警阈值
if error_rate > 0.1:  # 错误率超过10%
    send_alert("ONLYOFFICE error rate high")
```

## 安全加固

### 1. 启用JWT验证（生产环境推荐）

```bash
# 生成JWT密钥
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 配置
ONLYOFFICE_JWT_ENABLED=true
ONLYOFFICE_JWT_SECRET=your_generated_secret
```

### 2. IP白名单

```python
# 限制代理端点访问
ALLOWED_IPS = ["101.37.24.171"]  # ONLYOFFICE服务器IP

@router.get("/download/file/{file_id}")
async def download_file(request: Request):
    client_ip = request.client.host
    if client_ip not in ALLOWED_IPS:
        raise HTTPException(403, "Access denied")
```

### 3. 使用HTTPS

```bash
# 配置SSL证书
# 使用Let's Encrypt或其他证书颁发机构
```

## 回滚方案

如果ONLYOFFICE集成出现问题，可以快速回滚：

### 1. 禁用ONLYOFFICE

```bash
# 修改 backend/.env
ONLYOFFICE_ENABLED=false
```

### 2. 恢复到华为云预览

系统会自动降级到华为云预览服务。

### 3. 重启服务

```bash
docker-compose restart backend
```

## 技术支持

### 文档资源
- [ONLYOFFICE API文档](https://api.onlyoffice.com/editors/basic)
- [ONLYOFFICE配置示例](https://api.onlyoffice.com/editors/config/)
- [项目实现文档](./ONLYOFFICE集成实现完成.md)

### 日志位置
- 后端日志：`backend/logs/app.log`
- ONLYOFFICE日志：ONLYOFFICE服务器上

### 联系方式
- 技术支持：[联系方式]
- 问题反馈：[GitHub Issues]

## 附录

### A. 完整配置示例

**backend/.env**：
```bash
# ONLYOFFICE配置
ONLYOFFICE_ENABLED=true
ONLYOFFICE_SERVER_URL=http://101.37.24.171:9090
ONLYOFFICE_JWT_ENABLED=false
ONLYOFFICE_CALLBACK_URL=http://123.45.67.89:8000/api/v1/onlyoffice/callback
BACKEND_PUBLIC_URL=http://123.45.67.89:8000
```

### B. 测试脚本

**test_onlyoffice.sh**：
```bash
#!/bin/bash

BACKEND_URL="http://your-backend-public-ip:8000"

echo "1. 测试后端健康检查..."
curl -s $BACKEND_URL/api/v1/onlyoffice/health | jq

echo "\n2. 测试代理端点..."
curl -I $BACKEND_URL/api/v1/onlyoffice/download/file/1

echo "\n3. 测试ONLYOFFICE服务..."
curl -s http://101.37.24.171:9090/healthcheck

echo "\n完成！"
```

### C. 故障排查流程图

```
编辑器加载失败
    ↓
检查ONLYOFFICE服务是否正常
    ↓ 正常
检查后端配置是否正确
    ↓ 正确
检查网络连通性
    ↓ 正常
检查防火墙规则
    ↓ 正确
查看后端日志
    ↓
定位具体错误
```

---

**文档版本**: 1.0
**更新日期**: 2026-01-03
**维护人员**: 技术团队
