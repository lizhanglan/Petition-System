# ONLYOFFICE本地开发限制说明

**问题时间**: 2026-01-03 22:45  
**问题**: 编辑器一直加载，无法显示文档  

---

## 🔴 问题根源

### 网络架构问题

**当前架构**:
```
浏览器 (localhost:5173)
    ↓
前端 (localhost:5173)
    ↓
后端 (localhost:8000) ← 本地运行
    ↓
MinIO (124.70.74.202:9000)
    ↑
ONLYOFFICE (101.37.24.171:9090) → 尝试访问 http://101.37.24.171:8000 ❌ 失败
```

**问题**:
1. 后端运行在 `localhost:8000`（本地）
2. ONLYOFFICE配置中的 `BACKEND_PUBLIC_URL=http://101.37.24.171:8000`
3. ONLYOFFICE服务器尝试访问 `http://101.37.24.171:8000/api/v1/onlyoffice/download/file/16`
4. 但是 `101.37.24.171:8000` 端口没有后端服务（后端在本地）
5. ONLYOFFICE无法下载文档，所以编辑器一直加载

### 为什么会这样？

ONLYOFFICE的工作流程：
1. 浏览器请求编辑器配置
2. 后端返回配置，包含文档URL：`http://101.37.24.171:8000/api/v1/onlyoffice/download/file/16`
3. ONLYOFFICE服务器（在 `101.37.24.171:9090`）尝试下载文档
4. ONLYOFFICE访问 `http://101.37.24.171:8000`（期望是后端）
5. **失败**：因为后端实际在 `localhost:8000`，不在 `101.37.24.171:8000`

---

## ✅ 解决方案

### 方案1：部署后端到公网服务器（生产环境）

**步骤**:
1. 将后端部署到 `101.37.24.171` 服务器
2. 后端监听 `8000` 端口
3. 确保防火墙开放 `8000` 端口
4. ONLYOFFICE就能访问后端代理端点

**优点**:
- ✅ ONLYOFFICE功能完全可用
- ✅ 符合生产环境架构
- ✅ 所有功能正常

**缺点**:
- ❌ 需要部署到服务器
- ❌ 本地开发不方便

---

### 方案2：本地开发时禁用ONLYOFFICE（推荐用于本地开发）

**步骤**:

1. **修改 `backend/.env`**:
```env
# ONLYOFFICE配置（本地开发时禁用）
ONLYOFFICE_ENABLED=false
```

2. **重启后端服务**:
```bash
# 停止当前后端
# 然后重新启动
cd backend
python run.py
```

3. **效果**:
- 系统自动降级到华为云预览
- 或者显示下载按钮
- 其他功能不受影响

**优点**:
- ✅ 本地开发方便
- ✅ 不需要部署
- ✅ 其他功能正常

**缺点**:
- ❌ 无法测试ONLYOFFICE功能
- ❌ 使用华为云预览（功能有限）

---

### 方案3：使用内网穿透（临时测试）

如果需要在本地测试ONLYOFFICE，可以使用内网穿透工具：

**工具选择**:
- ngrok
- frp
- localtunnel

**步骤（以ngrok为例）**:

1. **安装ngrok**:
```bash
# 下载并安装 ngrok
# https://ngrok.com/download
```

2. **启动内网穿透**:
```bash
ngrok http 8000
```

3. **获取公网URL**:
```
Forwarding  https://xxxx.ngrok.io -> http://localhost:8000
```

4. **修改配置**:
```env
BACKEND_PUBLIC_URL=https://xxxx.ngrok.io
ONLYOFFICE_CALLBACK_URL=https://xxxx.ngrok.io/api/v1/onlyoffice/callback
```

5. **重启后端**

**优点**:
- ✅ 可以在本地测试ONLYOFFICE
- ✅ 不需要部署到服务器

**缺点**:
- ❌ 需要额外工具
- ❌ URL会变化
- ❌ 可能有性能问题
- ❌ 免费版有限制

---

## 📋 当前推荐方案

### 本地开发阶段

**禁用ONLYOFFICE，使用华为云降级**:

1. 修改 `backend/.env`:
```env
ONLYOFFICE_ENABLED=false
```

2. 重启后端服务

3. 系统会自动使用华为云预览

4. 开发其他功能不受影响

### 部署到服务器后

**启用ONLYOFFICE**:

1. 确保后端部署到 `101.37.24.171:8000`

2. 修改 `backend/.env`:
```env
ONLYOFFICE_ENABLED=true
BACKEND_PUBLIC_URL=http://101.37.24.171:8000
```

3. 重启后端服务

4. ONLYOFFICE功能完全可用

---

## 🔧 快速操作

### 禁用ONLYOFFICE（本地开发）

```bash
# 1. 编辑配置文件
notepad backend\.env

# 2. 修改这一行
ONLYOFFICE_ENABLED=false

# 3. 保存并重启后端
cd backend
python run.py
```

### 启用ONLYOFFICE（服务器部署）

```bash
# 1. 编辑配置文件
vi backend/.env

# 2. 修改这一行
ONLYOFFICE_ENABLED=true

# 3. 确保后端URL正确
BACKEND_PUBLIC_URL=http://101.37.24.171:8000

# 4. 保存并重启后端
cd backend
python run.py
```

---

## 📊 功能对比

| 功能 | ONLYOFFICE禁用 | ONLYOFFICE启用 |
|------|---------------|---------------|
| 文件预览 | ✅ 华为云 | ✅ ONLYOFFICE |
| 文件编辑 | ❌ | ✅ |
| 文书预览 | ✅ 华为云 | ✅ ONLYOFFICE |
| 文书编辑 | ✅ 富文本编辑器 | ✅ ONLYOFFICE |
| 文件研判 | ✅ | ✅ |
| 协同编辑 | ❌ | ✅ |
| 本地开发 | ✅ 方便 | ❌ 需要穿透 |
| 服务器部署 | ✅ | ✅ |

---

## 🎯 总结

### 问题本质
ONLYOFFICE是服务器端组件，需要能够访问后端API。本地开发时，后端在 `localhost`，ONLYOFFICE无法访问。

### 解决方案
- **本地开发**: 禁用ONLYOFFICE，使用华为云降级
- **服务器部署**: 启用ONLYOFFICE，完整功能

### 下一步
1. 当前在本地开发，建议禁用ONLYOFFICE
2. 继续开发其他功能
3. 部署到服务器后再启用ONLYOFFICE
4. 进行完整的功能测试

---

## 📝 配置文件示例

### 本地开发配置
```env
# backend/.env
ONLYOFFICE_ENABLED=false
ONLYOFFICE_SERVER_URL=http://101.37.24.171:9090
BACKEND_PUBLIC_URL=http://101.37.24.171:8000
```

### 服务器部署配置
```env
# backend/.env（在101.37.24.171服务器上）
ONLYOFFICE_ENABLED=true
ONLYOFFICE_SERVER_URL=http://101.37.24.171:9090
BACKEND_PUBLIC_URL=http://101.37.24.171:8000
ONLYOFFICE_CALLBACK_URL=http://101.37.24.171:8000/api/v1/onlyoffice/callback
```

---

**创建时间**: 2026-01-03 22:45  
**文档版本**: 1.0
