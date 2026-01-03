# WPS文档处理集成指南

**更新日期**: 2026-01-03  
**版本**: 1.0

---

## 📋 概述

本系统已集成WPS开放平台，支持使用WPS原生接口进行文档预览和在线编辑。

---

## 🎯 功能特性

### ✅ 已实现
- 文档在线预览（WPS原生渲染）
- 文档在线编辑（完整Word功能）
- 自动保存回调
- 签名验证机制
- 配置开关控制

### 🔄 与现有功能对比

| 功能 | 富文本编辑器 | 华为云预览 | WPS服务 |
|-----|------------|-----------|---------|
| 文档预览 | ❌ | ✅ | ✅ |
| 在线编辑 | ✅ 基础 | ❌ | ✅ 专业 |
| 格式保留 | HTML | 完整 | 完整 |
| 协同编辑 | ❌ | ❌ | ✅ |
| 打印预览 | ❌ | ✅ | ✅ |
| 页面设置 | ❌ | ❌ | ✅ |

---

## 🚀 快速开始

### 1. 申请WPS开放平台账号

访问: https://open.wps.cn/

1. 注册并完成企业认证
2. 创建应用
3. 获取App ID和App Secret

### 2. 配置系统

编辑 `.env` 文件：

```bash
# WPS开放平台配置
WPS_APP_ID=your_app_id_here
WPS_APP_SECRET=your_app_secret_here
WPS_API_BASE=https://open.wps.cn
WPS_ENABLED=true
```

### 3. 重启服务

```bash
# Docker部署
docker-compose restart backend

# 本地开发
cd backend
python run.py
```

### 4. 测试功能

1. 登录系统
2. 进入文书管理
3. 点击"查看"或"编辑"
4. 系统会自动使用WPS服务

---

## 📝 API接口

### 1. 获取预览URL

**端点**: `POST /api/v1/wps/preview`

**请求**:
```json
{
  "document_id": 1
}
```

**响应**:
```json
{
  "preview_url": "https://wps.cn/preview/...",
  "file_url": "http://...",
  "file_name": "文档.docx"
}
```

### 2. 获取编辑URL

**端点**: `POST /api/v1/wps/edit`

**请求**:
```json
{
  "document_id": 1
}
```

**响应**:
```json
{
  "edit_url": "https://wps.cn/edit/...",
  "token": "...",
  "expires_in": 3600
}
```

### 3. 保存回调

**端点**: `POST /api/v1/wps/callback`

WPS服务器会在用户保存文档后调用此接口。

---

## 🔧 配置说明

### 环境变量

| 变量名 | 说明 | 必填 | 默认值 |
|-------|------|------|--------|
| WPS_APP_ID | WPS应用ID | 是 | - |
| WPS_APP_SECRET | WPS应用密钥 | 是 | - |
| WPS_API_BASE | WPS API地址 | 否 | https://open.wps.cn |
| WPS_ENABLED | 是否启用WPS | 否 | false |

### 启用/禁用WPS服务

```bash
# 启用
WPS_ENABLED=true

# 禁用（使用华为云或富文本编辑器）
WPS_ENABLED=false
```

---

## 🔒 安全机制

### 1. 签名验证
所有API请求都使用MD5签名验证，防止请求篡改。

### 2. Token机制
编辑URL包含临时token，有效期1小时。

### 3. 回调验证
验证回调签名，确保回调来自WPS服务器。

### 4. 权限控制
用户只能访问自己的文档。

---

## 📊 工作流程

### 预览流程

```
用户点击预览
    ↓
前端调用 /wps/preview
    ↓
后端生成DOCX文件
    ↓
上传到MinIO
    ↓
调用WPS API获取预览URL
    ↓
返回预览URL
    ↓
前端iframe显示WPS预览
```

### 编辑流程

```
用户点击编辑
    ↓
前端调用 /wps/edit
    ↓
后端生成DOCX文件
    ↓
上传到MinIO
    ↓
调用WPS API获取编辑URL
    ↓
返回编辑URL和token
    ↓
前端打开WPS编辑器
    ↓
用户编辑文档
    ↓
WPS自动保存
    ↓
WPS回调 /wps/callback
    ↓
后端更新文档
```

---

## 🐛 故障排查

### 问题1: 无法获取WPS URL

**检查**:
1. WPS_ENABLED是否为true
2. WPS_APP_ID和WPS_APP_SECRET是否正确
3. 网络是否可以访问WPS服务器

**解决**:
```bash
# 检查配置
cat .env | grep WPS

# 测试网络
curl https://open.wps.cn

# 查看日志
docker-compose logs backend | grep WPS
```

### 问题2: 预览显示"无法加载文件"

**检查**:
1. MinIO是否可以公网访问
2. 文件URL是否有效
3. 文件是否已过期

**解决**:
```bash
# 配置MinIO公网地址
MINIO_PUBLIC_URL=http://your-server-ip:9000

# 测试文件访问
curl http://your-server-ip:9000/bucket/file.docx
```

### 问题3: 编辑后无法保存

**检查**:
1. 回调URL是否可以公网访问
2. 回调URL配置是否正确
3. 签名验证是否通过

**解决**:
```bash
# 检查回调URL
# 确保 http://your-domain/api/v1/wps/callback 可以访问

# 查看回调日志
docker-compose logs backend | grep "WPS Callback"
```

---

## 💡 最佳实践

### 1. 生产环境配置

```bash
# 使用HTTPS
WPS_API_BASE=https://open.wps.cn

# 配置公网MinIO地址
MINIO_PUBLIC_URL=https://files.yourdomain.com

# 启用WPS服务
WPS_ENABLED=true
```

### 2. 开发环境配置

```bash
# 禁用WPS服务（使用富文本编辑器）
WPS_ENABLED=false

# 或使用华为云预览
# 配置华为云凭证
```

### 3. 混合部署

```python
# 在代码中实现降级逻辑
if settings.WPS_ENABLED:
    # 使用WPS服务
    preview_url = await wps_service.get_preview_url(...)
else:
    # 使用华为云服务
    preview_url = await office_preview_service.get_preview_url(...)
```

---

## 📚 相关文档

- **WPS开放平台文档**: https://open.wps.cn/docs/
- **技术实现文档**: `docs/development/WPS文档处理集成完成.md`
- **API文档**: 访问 http://localhost:8000/docs 查看Swagger文档

---

## ✅ 检查清单

部署前请确认：

- [ ] 已申请WPS开放平台账号
- [ ] 已创建WPS应用
- [ ] 已获取App ID和App Secret
- [ ] 已配置.env文件
- [ ] 已设置WPS_ENABLED=true
- [ ] MinIO可以公网访问
- [ ] 回调URL可以公网访问
- [ ] 已测试预览功能
- [ ] 已测试编辑功能

---

## 🆘 技术支持

如遇到问题：

1. 查看日志: `docker-compose logs backend | grep WPS`
2. 检查配置: `cat .env | grep WPS`
3. 测试网络: `curl https://open.wps.cn`
4. 查看文档: `docs/development/WPS文档处理集成完成.md`

---

**更新时间**: 2026-01-03  
**文档版本**: 1.0  
**状态**: ✅ 已完成，可以使用


---

## 🔄 预览服务优先级（2026-01-03更新）

系统现在使用智能预览服务选择器（`preview_service_selector`），自动选择最优的预览服务。

### 优先级顺序

1. **WPS服务**（如果启用）- 功能最完整，支持预览和编辑
2. **华为云服务**（降级方案）- 稳定可靠的备选方案
3. **直接URL**（仅PDF）- 浏览器原生支持
4. **不支持预览**（其他格式）

### 自动降级机制

```
检查WPS_ENABLED配置
    ↓
WPS_ENABLED=true → 尝试WPS服务
    ↓
WPS成功 → 返回WPS预览URL ✅
    ↓
WPS失败 → 降级到华为云服务
    ↓
华为云成功 → 返回华为云预览URL ✅
    ↓
华为云失败 → 检查文件类型
    ↓
PDF文件 → 返回直接URL（浏览器预览）✅
    ↓
其他格式 → 返回不支持预览 ❌
```

### 服务类型标识

API返回的`service_type`字段标识当前使用的服务：

| service_type | 说明 | 功能 |
|-------------|------|------|
| `wps` | WPS服务 | 完整预览和编辑功能 |
| `huawei` | 华为云服务 | 预览功能 |
| `direct` | 直接URL | PDF浏览器原生预览 |
| `unsupported` | 不支持预览 | 仅提供下载 |

### 代码示例

#### 后端使用（推荐）

```python
from app.services.preview_service_selector import preview_service_selector

# 获取预览URL（自动处理降级）
preview_result = await preview_service_selector.get_preview_url(
    file_url="https://your-minio.com/bucket/file.docx",
    file_name="文档.docx",
    user_id="user_123",
    permission="read"
)

# 返回格式
# {
#     "preview_url": "https://...",
#     "service_type": "wps",  # 或 "huawei", "direct", "unsupported"
#     "file_url": "https://..."
# }

# 获取编辑URL（仅WPS支持）
edit_result = await preview_service_selector.get_edit_url(
    file_url="https://your-minio.com/bucket/file.docx",
    file_name="文档.docx",
    user_id="user_123",
    user_name="张三",
    callback_url="https://your-api.com/api/v1/wps/callback"
)

# 返回格式
# {
#     "edit_url": "https://...",
#     "token": "...",
#     "expires_in": 3600,
#     "service_type": "wps"
# }
```

#### 前端处理

```javascript
// 获取预览
const response = await api.get(`/api/v1/files/${fileId}/preview`);

// 根据service_type处理
switch (response.data.service_type) {
  case 'wps':
    // WPS预览，功能最完整
    console.log('使用WPS预览服务');
    showPreview(response.data.preview_url);
    break;
    
  case 'huawei':
    // 华为云预览
    console.log('使用华为云预览服务');
    showPreview(response.data.preview_url);
    break;
    
  case 'direct':
    // PDF直接预览
    console.log('使用浏览器直接预览');
    showPreview(response.data.preview_url);
    break;
    
  case 'unsupported':
    // 不支持预览，提供下载
    console.log('不支持预览，提供下载');
    showDownloadButton(response.data.file_url);
    break;
}
```

### 日志监控

系统会输出详细的服务选择日志：

```
[PreviewSelector] 尝试使用WPS服务...
[WPS] Requesting preview URL for: 文档.docx
[WPS] Response status: 200
[WPS] Success: https://wps.cn/preview/...
[PreviewSelector] WPS服务成功: https://...
```

降级时的日志：

```
[PreviewSelector] 尝试使用WPS服务...
[WPS] Response status: 500
[PreviewSelector] WPS服务返回空URL，尝试降级...
[PreviewSelector] 使用华为云预览服务...
[Preview Service] Requesting preview for URL: https://...
[Preview Service] Success: https://huawei.com/preview/...
[PreviewSelector] 华为云服务成功: https://...
```

### 优势

#### 1. 高可用性
- 双重保障，降低单点故障风险
- WPS失败时自动切换到华为云
- 提高系统整体可用性

#### 2. 功能完整性
- WPS提供最完整的预览和编辑功能
- 华为云作为稳定的备选方案
- PDF文件支持浏览器原生预览

#### 3. 灵活配置
- 通过`WPS_ENABLED`开关控制
- 可以根据实际情况选择服务
- 配置简单，易于维护

#### 4. 透明降级
- 自动处理服务切换
- 前端无需关心具体使用哪个服务
- 统一的API接口

### 测试建议

#### 测试WPS服务

```bash
# 1. 启用WPS服务
WPS_ENABLED=true
WPS_APP_ID=your_app_id
WPS_APP_SECRET=your_app_secret

# 2. 重启服务
docker-compose restart backend

# 3. 上传文件并预览
# 4. 检查日志是否显示"WPS服务成功"
docker-compose logs backend | grep "WPS服务成功"
```

#### 测试降级机制

```bash
# 方法1: 禁用WPS服务
WPS_ENABLED=false

# 方法2: 使用错误的WPS配置
WPS_APP_ID=invalid
WPS_APP_SECRET=invalid

# 重启并测试
docker-compose restart backend

# 检查日志是否显示降级
docker-compose logs backend | grep "降级"
```

#### 测试完全失败

```bash
# 同时禁用WPS和华为云
WPS_ENABLED=false
OFFICE_HTTP=http://invalid

# 测试PDF文件（应返回direct）
# 测试Word文件（应返回unsupported）
```

### 注意事项

#### 1. 文件URL要求
- 文件URL必须是公网可访问的
- MinIO需要配置正确的外网地址
- 确保WPS和华为云都能访问到文件

```bash
# 配置MinIO公网地址
MINIO_ENDPOINT=your-server-ip:9000
# 或使用域名
MINIO_ENDPOINT=files.yourdomain.com
```

#### 2. 性能考虑
- WPS服务调用有超时时间（30秒）
- 降级会增加响应时间（需要等待WPS超时）
- 建议监控服务响应时间

#### 3. 成本考虑
- WPS服务可能有调用次数限制
- 华为云服务按调用次数计费
- 合理配置降级策略

#### 4. 日志监控
- 关注服务降级频率
- 如果频繁降级，检查WPS配置
- 监控华为云服务可用性

### 相关文档

- **预览服务优先级集成**: `docs/development/WPS预览服务优先级集成完成.md`
- **WPS服务实现**: `backend/app/services/wps_service.py`
- **预览服务选择器**: `backend/app/services/preview_service_selector.py`
- **华为云服务**: `backend/app/services/office_preview_service.py`

---

**最后更新**: 2026-01-03  
**更新内容**: 添加预览服务优先级和自动降级机制
