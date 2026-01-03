# ONLYOFFICE集成快速参考卡

## 🚀 5分钟快速配置

### 1. 配置环境变量（backend/.env）
```bash
ONLYOFFICE_ENABLED=true
ONLYOFFICE_SERVER_URL=http://101.37.24.171:9090
ONLYOFFICE_JWT_ENABLED=false
ONLYOFFICE_CALLBACK_URL=http://YOUR_PUBLIC_IP:8000/api/v1/onlyoffice/callback
BACKEND_PUBLIC_URL=http://YOUR_PUBLIC_IP:8000
```

### 2. 重启后端
```bash
cd backend
python run.py
```

### 3. 测试验证
打开 `test_onlyoffice_with_backend.html`

---

## 📋 核心API端点

### 获取编辑器配置
```bash
POST /api/v1/onlyoffice/config
{
  "file_id": 1,        # 或 "document_id": 1
  "mode": "edit"       # "view" 或 "edit"
}
```

### 文件下载代理（供ONLYOFFICE访问）
```bash
GET /api/v1/onlyoffice/download/file/{file_id}
GET /api/v1/onlyoffice/download/document/{document_id}
```

### 保存回调
```bash
POST /api/v1/onlyoffice/callback?fileId={id}&type=file
```

### 健康检查
```bash
GET /api/v1/onlyoffice/health
```

---

## 💻 前端使用

### 导入组件
```vue
<script setup>
import OnlyOfficeEditor from '@/components/OnlyOfficeEditor.vue'
</script>
```

### 使用组件
```vue
<template>
  <!-- 文件预览/编辑 -->
  <OnlyOfficeEditor
    :file-id="123"
    mode="edit"
    height="600px"
    @error="handleError"
  />
  
  <!-- 文书预览/编辑 -->
  <OnlyOfficeEditor
    :document-id="456"
    mode="view"
    @error="handleError"
  />
</template>
```

---

## 🔧 常见问题速查

### ❌ 错误代码-4（下载失败）
**原因**: ONLYOFFICE无法访问后端  
**解决**: 
1. 检查 `BACKEND_PUBLIC_URL` 配置
2. 测试: `curl http://YOUR_PUBLIC_IP:8000/api/v1/onlyoffice/health`
3. 检查防火墙规则

### ❌ 保存回调失败
**原因**: ONLYOFFICE无法访问回调URL  
**解决**: 
1. 检查 `ONLYOFFICE_CALLBACK_URL` 配置
2. 确保使用公网IP而非localhost

### ❌ 后端没有公网IP
**解决**: 使用ngrok内网穿透
```bash
ngrok http 8000
# 使用返回的URL配置BACKEND_PUBLIC_URL
```

---

## 📊 架构速览

```
用户浏览器 → ONLYOFFICE服务器 → 后端代理 → MinIO
           (101.37.24.171)    (公网IP)   (内网)
```

**关键点**:
- ONLYOFFICE通过后端代理访问文件
- 后端必须有公网IP
- 防火墙允许ONLYOFFICE访问后端

---

## ✅ 配置检查清单

- [ ] `ONLYOFFICE_ENABLED=true`
- [ ] `BACKEND_PUBLIC_URL` 配置为公网IP ⚠️
- [ ] `ONLYOFFICE_CALLBACK_URL` 配置为公网IP ⚠️
- [ ] 后端有公网访问能力
- [ ] 防火墙允许101.37.24.171访问后端8000端口
- [ ] 测试页面加载成功

---

## 📚 完整文档

- [实现完成报告](docs/development/ONLYOFFICE集成实现完成.md)
- [部署配置指南](docs/deployment/ONLYOFFICE部署配置指南.md)
- [集成完成总结](ONLYOFFICE集成完成总结.md)

---

## 🎯 下一步

1. **立即**: 配置 `BACKEND_PUBLIC_URL`（10分钟）
2. **测试**: 使用测试页面验证（30分钟）
3. **集成**: 更新前端页面（3.5小时）

---

**快速支持**: 查看 `ONLYOFFICE集成完成总结.md`
