# WPS预览服务集成完成 - 快速参考

**完成时间**: 2026-01-03  
**状态**: ✅ 已完成，可以使用

---

## 🎯 核心改进

项目现在使用**智能预览服务选择器**，自动选择最优的预览服务：

```
WPS服务（优先） → 华为云服务（降级） → 直接URL（PDF） → 不支持
```

---

## 📁 修改的文件

### 新增文件（1个）
- `backend/app/services/preview_service_selector.py` - 预览服务选择器

### 修改文件（2个）
- `backend/app/api/v1/endpoints/files.py` - 文件管理接口
- `backend/app/api/v1/endpoints/documents.py` - 文书管理接口

### 文档文件（4个）
- `docs/development/WPS预览服务优先级集成完成.md` - 完整实现文档
- `docs/development/2026-01-03-WPS预览服务集成总结.md` - 简要总结
- `WPS_INTEGRATION_GUIDE.md` - WPS集成指南（已更新）
- `WPS预览服务集成完成-快速参考.md` - 本文档

---

## ⚙️ 配置方法

### 启用WPS服务（推荐）

编辑 `.env` 文件：
```bash
WPS_APP_ID=your_app_id_here
WPS_APP_SECRET=your_app_secret_here
WPS_ENABLED=true
```

重启服务：
```bash
docker-compose restart backend
```

### 禁用WPS服务（使用华为云）

编辑 `.env` 文件：
```bash
WPS_ENABLED=false
```

---

## 🔍 如何验证

### 1. 检查配置
```bash
cat .env | grep WPS
```

应该看到：
```
WPS_APP_ID=...
WPS_APP_SECRET=...
WPS_ENABLED=true
```

### 2. 查看日志
```bash
docker-compose logs backend | grep -i "preview"
```

成功时应该看到：
```
[PreviewSelector] 尝试使用WPS服务...
[WPS] Success: https://...
[PreviewSelector] WPS服务成功
```

降级时应该看到：
```
[PreviewSelector] WPS服务返回空URL，尝试降级...
[PreviewSelector] 使用华为云预览服务...
[PreviewSelector] 华为云服务成功
```

### 3. 测试功能
1. 登录系统
2. 上传一个Word文档
3. 点击"预览"
4. 检查是否能正常预览

---

## 📊 API变化

### 文件预览接口
**端点**: `GET /api/v1/files/{file_id}/preview`

**新增返回字段**:
```json
{
  "preview_url": "https://...",
  "service_type": "wps",  // 新增：标识使用的服务
  "file_url": "https://...",
  "file_type": "docx",
  "file_name": "文档.docx"
}
```

**service_type可能的值**:
- `wps` - 使用WPS服务
- `huawei` - 使用华为云服务
- `direct` - 直接URL（PDF）
- `unsupported` - 不支持预览

### 文书预览接口
**端点**: `GET /api/v1/documents/{document_id}/preview`

**新增返回字段**:
```json
{
  "preview_url": "https://...",
  "service_type": "wps",  // 新增
  "file_url": "https://...",
  "document_id": 123
}
```

---

## 🚨 注意事项

### 1. WPS服务要求
- 需要在WPS开放平台注册应用
- 文件URL必须是公网可访问的
- MinIO需要配置正确的外网地址

### 2. 降级机制
- WPS失败时自动切换到华为云
- 华为云失败时，PDF返回直接URL
- 所有服务失败时，返回不支持预览

### 3. 性能影响
- WPS调用有30秒超时
- 降级会增加响应时间
- 建议监控服务响应时间

---

## 🔧 故障排查

### 问题1: 无法使用WPS预览

**检查步骤**:
```bash
# 1. 检查配置
cat .env | grep WPS_ENABLED
# 应该是: WPS_ENABLED=true

# 2. 检查凭证
cat .env | grep WPS_APP
# 应该有: WPS_APP_ID 和 WPS_APP_SECRET

# 3. 查看日志
docker-compose logs backend | grep WPS
```

**解决方法**:
- 确保WPS_ENABLED=true
- 确保WPS_APP_ID和WPS_APP_SECRET正确
- 检查网络是否能访问WPS服务器

### 问题2: 频繁降级到华为云

**可能原因**:
- WPS配置错误
- WPS服务不可用
- 文件URL无法访问

**解决方法**:
```bash
# 测试WPS服务
curl https://open.wps.cn

# 测试文件URL
curl http://your-minio-url/bucket/file.docx

# 查看详细日志
docker-compose logs backend | grep -A 5 "PreviewSelector"
```

### 问题3: 所有服务都失败

**检查步骤**:
```bash
# 1. 检查MinIO
docker-compose ps minio

# 2. 检查MinIO配置
cat .env | grep MINIO

# 3. 测试MinIO访问
curl http://localhost:9000
```

---

## 📚 详细文档

### 完整实现文档
→ `docs/development/WPS预览服务优先级集成完成.md`

### WPS集成指南
→ `WPS_INTEGRATION_GUIDE.md`

### 代码实现
→ `backend/app/services/preview_service_selector.py`

---

## ✅ 检查清单

部署前请确认：

- [ ] 已配置WPS_APP_ID和WPS_APP_SECRET
- [ ] 已设置WPS_ENABLED=true
- [ ] MinIO可以公网访问
- [ ] 已重启后端服务
- [ ] 已测试文件预览功能
- [ ] 已测试文书预览功能
- [ ] 已查看日志确认服务正常

---

## 🎉 总结

成功实现了预览服务的智能选择和自动降级：

✅ **高可用性** - 双重保障，降低故障风险  
✅ **功能完整** - WPS提供最完整的功能  
✅ **灵活配置** - 简单开关控制  
✅ **透明降级** - 自动处理，无需人工干预  
✅ **向后兼容** - 不影响现有功能  

---

**状态**: ✅ 已完成  
**测试**: ⚠️ 需要配置WPS后测试  
**部署**: ✅ 可以部署
