# ONLYOFFICE重构任务清单

## 任务优先级说明
- 🔴 P0：必须完成，阻塞性任务
- 🟡 P1：重要任务，核心功能
- 🟢 P2：优化任务，增强功能

---

## 阶段一：环境准备与验证（1天）

### ✅ 任务1.1：验证ONLYOFFICE服务 🔴 P0
**负责人**：后端开发
**预计时间**：2小时

**检查项**：
- [ ] 访问 `http://101.37.24.171:9090` 确认服务可用
- [ ] 测试 `/healthcheck` 端点
- [ ] 确认支持的文档格式（docx, xlsx, pptx, pdf）
- [ ] 检查是否已启用JWT验证
- [ ] 记录ONLYOFFICE版本信息

**验证脚本**：
```bash
# 健康检查
curl http://101.37.24.171:9090/healthcheck

# 测试API端点
curl http://101.37.24.171:9090/web-apps/apps/api/documents/api.js
```

**输出**：
- ONLYOFFICE服务状态报告
- 支持的功能列表

---

### ✅ 任务1.2：生成和配置JWT密钥 🔴 P0
**负责人**：后端开发
**预计时间**：1小时

**步骤**：
- [ ] 生成安全的JWT密钥
- [ ] 在ONLYOFFICE服务器配置JWT（如需要）
- [ ] 更新 `.env` 文件
- [ ] 更新 `.env.example` 文件
- [ ] 验证JWT配置生效

**代码**：
```python
import secrets
jwt_secret = secrets.token_urlsafe(32)
```

**配置文件**：
```bash
# .env
ONLYOFFICE_ENABLED=true
ONLYOFFICE_SERVER_URL=http://101.37.24.171:9090
ONLYOFFICE_JWT_SECRET=生成的密钥
ONLYOFFICE_JWT_ENABLED=true
```

---

### ✅ 任务1.3：安装Python依赖 🔴 P0
**负责人**：后端开发
**预计时间**：30分钟

**步骤**：
- [ ] 添加 `PyJWT` 到 `requirements.txt`
- [ ] 安装依赖：`pip install PyJWT`
- [ ] 验证导入成功

**requirements.txt**：
```
PyJWT==2.8.0
```

---

## 阶段二：后端核心服务开发（3天）

### ✅ 任务2.1：更新配置类 🔴 P0
**负责人**：后端开发
**预计时间**：1小时

**文件**：`backend/app/core/config.py`

**任务**：
- [ ] 添加ONLYOFFICE配置字段
- [ ] 添加配置验证逻辑
- [ ] 更新配置文档注释

**代码**：
```python
# ONLYOFFICE配置
ONLYOFFICE_ENABLED: bool = True
ONLYOFFICE_SERVER_URL: str = "http://101.37.24.171:9090"
ONLYOFFICE_JWT_SECRET: str = ""
ONLYOFFICE_JWT_ENABLED: bool = True
ONLYOFFICE_CALLBACK_URL: str = ""  # 回调URL，如：http://your-backend/api/v1/onlyoffice/callback
```

---

### ✅ 任务2.2：创建ONLYOFFICE服务类 🔴 P0
**负责人**：后端开发
**预计时间**：1天

**文件**：`backend/app/services/onlyoffice_service.py`

**功能清单**：
- [ ] 生成编辑器配置JSON
- [ ] 生成JWT token
- [ ] 验证JWT token
- [ ] 处理文档保存回调
- [ ] 支持预览模式（view）
- [ ] 支持编辑模式（edit）
- [ ] 错误处理和日志记录

**核心方法**：
```python
class OnlyOfficeService:
    async def get_editor_config(
        self,
        file_id: int,
        file_url: str,
        file_name: str,
        file_type: str,
        user_id: str,
        user_name: str,
        mode: str = 'view'  # 'view' or 'edit'
    ) -> dict
    
    async def generate_jwt_token(self, payload: dict) -> str
    
    async def verify_jwt_token(self, token: str) -> dict
    
    async def handle_callback(
        self,
        callback_data: dict,
        file_id: int,
        user_id: int
    ) -> dict
    
    def _get_document_type(self, file_extension: str) -> str
```

**配置JSON结构**：
```json
{
  "document": {
    "fileType": "docx",
    "key": "unique_key",
    "title": "文档.docx",
    "url": "http://backend/api/v1/onlyoffice/download/123",
    "permissions": {
      "edit": true,
      "download": true,
      "print": true
    }
  },
  "documentType": "word",
  "editorConfig": {
    "mode": "edit",
    "lang": "zh-CN",
    "callbackUrl": "http://backend/api/v1/onlyoffice/callback",
    "user": {
      "id": "user_123",
      "name": "张三"
    },
    "customization": {
      "autosave": true,
      "forcesave": true,
      "comments": true,
      "chat": false
    }
  },
  "token": "jwt_token_here"
}
```

---

### ✅ 任务2.3：创建ONLYOFFICE API端点 🔴 P0
**负责人**：后端开发
**预计时间**：1天

**文件**：`backend/app/api/v1/endpoints/onlyoffice.py`

**端点清单**：

#### 1. 获取编辑器配置
```python
@router.post("/config")
async def get_editor_config(
    file_id: int,
    mode: str = 'view',  # 'view' or 'edit'
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
)
```

#### 2. 文件下载（供ONLYOFFICE访问）
```python
@router.get("/download/{file_id}")
async def download_file_for_onlyoffice(
    file_id: int,
    token: str,  # JWT token验证
    db: AsyncSession = Depends(get_db)
)
```

#### 3. 保存回调
```python
@router.post("/callback")
async def handle_save_callback(
    request: Request,
    db: AsyncSession = Depends(get_db)
)
```

#### 4. 健康检查
```python
@router.get("/health")
async def health_check()
```

**任务**：
- [ ] 实现所有端点
- [ ] 添加权限验证
- [ ] 添加错误处理
- [ ] 添加审计日志
- [ ] 编写API文档注释

---

### ✅ 任务2.4：注册ONLYOFFICE路由 🔴 P0
**负责人**：后端开发
**预计时间**：30分钟

**文件**：`backend/app/api/v1/__init__.py`

**任务**：
- [ ] 导入onlyoffice路由
- [ ] 注册到API路由器
- [ ] 验证路由可访问

**代码**：
```python
from app.api.v1.endpoints import onlyoffice

api_router.include_router(
    onlyoffice.router,
    prefix="/onlyoffice",
    tags=["onlyoffice"]
)
```

---

### ✅ 任务2.5：更新预览服务选择器 🟡 P1
**负责人**：后端开发
**预计时间**：3小时

**文件**：`backend/app/services/preview_service_selector.py`

**改动**：
- [ ] 添加ONLYOFFICE作为首选服务
- [ ] 保留华为云作为降级服务
- [ ] 更新 `get_preview_url` 方法
- [ ] 更新 `get_edit_url` 方法
- [ ] 添加服务切换日志

**优先级逻辑**：
```
1. ONLYOFFICE（支持预览和编辑）
2. 华为云（仅预览，降级）
3. 直接URL（PDF文件）
```

---

## 阶段三：前端组件开发（3天）

### ✅ 任务3.1：创建ONLYOFFICE编辑器组件 🔴 P0
**负责人**：前端开发
**预计时间**：1天

**文件**：`frontend/src/components/OnlyOfficeEditor.vue`

**功能清单**：
- [ ] 加载ONLYOFFICE API脚本
- [ ] 初始化编辑器
- [ ] 支持预览模式
- [ ] 支持编辑模式
- [ ] 处理编辑器事件（保存、关闭、错误）
- [ ] 显示加载状态
- [ ] 错误处理和提示

**组件接口**：
```vue
<template>
  <div class="onlyoffice-editor">
    <div v-if="loading" class="loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>正在加载编辑器...</span>
    </div>
    <div v-else-if="error" class="error">
      <el-alert :title="error" type="error" />
    </div>
    <div v-else id="onlyoffice-editor-container"></div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  fileId: number
  mode?: 'view' | 'edit'
  height?: string
}

interface Emits {
  (e: 'save', data: any): void
  (e: 'close'): void
  (e: 'error', error: string): void
}
</script>
```

**关键方法**：
- `loadOnlyOfficeScript()` - 加载ONLYOFFICE API
- `initEditor()` - 初始化编辑器
- `destroyEditor()` - 销毁编辑器
- `handleDocumentReady()` - 文档加载完成
- `handleError()` - 错误处理

---

### ✅ 任务3.2：创建API调用方法 🔴 P0
**负责人**：前端开发
**预计时间**：2小时

**文件**：`frontend/src/api/onlyoffice.ts`

**方法清单**：
```typescript
// 获取编辑器配置
export const getEditorConfig = (fileId: number, mode: 'view' | 'edit') => {
  return request.post('/onlyoffice/config', { file_id: fileId, mode })
}

// 检查ONLYOFFICE服务状态
export const checkOnlyOfficeHealth = () => {
  return request.get('/onlyoffice/health')
}
```

---

### ✅ 任务3.3：更新文件预览页面 🟡 P1
**负责人**：前端开发
**预计时间**：4小时

**文件**：`frontend/src/views/Files.vue`

**改动清单**：
- [ ] 导入OnlyOfficeEditor组件
- [ ] 替换现有预览iframe
- [ ] 添加"在线编辑"按钮
- [ ] 处理编辑完成事件
- [ ] 刷新文件列表
- [ ] 更新UI样式

**代码示例**：
```vue
<template>
  <el-dialog v-model="previewVisible" title="文件预览" fullscreen>
    <OnlyOfficeEditor
      v-if="currentFileId"
      :file-id="currentFileId"
      :mode="editMode ? 'edit' : 'view'"
      @save="handleFileSaved"
      @close="previewVisible = false"
    />
  </el-dialog>
</template>
```

---

### ✅ 任务3.4：更新文书生成预览 🟡 P1
**负责人**：前端开发
**预计时间**：4小时

**文件**：`frontend/src/views/Generate.vue`

**改动清单**：
- [ ] 右侧预览区使用OnlyOfficeEditor
- [ ] 支持生成后立即编辑
- [ ] 编辑后自动保存到文档库
- [ ] 更新预览加载逻辑
- [ ] 优化用户体验

**关键改动**：
```vue
<el-col :span="12">
  <el-card>
    <template #header>
      <div class="card-header">
        <span>生成预览</span>
        <div v-if="currentDocumentId">
          <el-button @click="editMode = !editMode" size="small">
            {{ editMode ? '切换到预览' : '在线编辑' }}
          </el-button>
        </div>
      </div>
    </template>
    
    <div class="preview-container">
      <OnlyOfficeEditor
        v-if="currentDocumentId"
        :file-id="currentDocumentId"
        :mode="editMode ? 'edit' : 'view'"
        @save="handleDocumentSaved"
      />
    </div>
  </el-card>
</el-col>
```

---

### ✅ 任务3.5：更新文书管理页面 🟡 P1
**负责人**：前端开发
**预计时间**：4小时

**文件**：`frontend/src/views/Documents.vue`

**改动清单**：
- [ ] 添加"在线编辑"按钮
- [ ] 使用OnlyOfficeEditor打开文书
- [ ] 支持编辑后保存
- [ ] 更新文档列表
- [ ] 显示编辑状态

---

### ✅ 任务3.6：更新文件研判页面 🟡 P1
**负责人**：前端开发
**预计时间**：3小时

**文件**：`frontend/src/views/Review.vue`

**改动清单**：
- [ ] 使用OnlyOfficeEditor显示文件
- [ ] 在编辑器中高亮显示问题（如可能）
- [ ] 优化预览体验

---

## 阶段四：功能增强（2天）

### ✅ 任务4.1：实现版本管理集成 🟢 P2
**负责人**：后端开发
**预计时间**：1天

**文件**：`backend/app/services/onlyoffice_service.py`

**功能**：
- [ ] 每次保存自动创建版本
- [ ] 在回调中创建Version记录
- [ ] 记录变更描述
- [ ] 支持版本对比

---

### ✅ 任务4.2：添加协作编辑支持 🟢 P2
**负责人**：后端开发
**预计时间**：1天

**功能**：
- [ ] 配置多用户编辑
- [ ] 显示在线用户
- [ ] 处理编辑冲突
- [ ] 实时同步

---

### ✅ 任务4.3：优化文档加载性能 🟢 P2
**负责人**：全栈
**预计时间**：4小时

**优化项**：
- [ ] 实现配置缓存
- [ ] 优化文件下载
- [ ] 添加预加载
- [ ] 压缩传输

---

## 阶段五：清理和优化（1天）

### ✅ 任务5.1：移除WPS服务代码 🟡 P1
**负责人**：后端开发
**预计时间**：2小时

**删除文件**：
- [ ] `backend/app/services/wps_service.py`
- [ ] `backend/app/api/v1/endpoints/wps.py`

**更新文件**：
- [ ] `backend/app/core/config.py` - 移除WPS配置
- [ ] `backend/app/services/preview_service_selector.py` - 移除WPS逻辑
- [ ] `.env.example` - 移除WPS配置项

---

### ✅ 任务5.2：更新文档 🟡 P1
**负责人**：技术文档
**预计时间**：3小时

**文档清单**：
- [ ] 更新README.md
- [ ] 更新部署文档
- [ ] 创建ONLYOFFICE配置指南
- [ ] 更新API文档
- [ ] 创建故障排查指南

---

### ✅ 任务5.3：代码审查和重构 🟢 P2
**负责人**：全栈
**预计时间**：3小时

**检查项**：
- [ ] 代码规范检查
- [ ] 错误处理完善
- [ ] 日志记录完善
- [ ] 性能优化
- [ ] 安全检查

---

## 阶段六：测试（2天）

### ✅ 任务6.1：单元测试 🔴 P0
**负责人**：后端开发
**预计时间**：1天

**测试文件**：`backend/tests/test_onlyoffice_service.py`

**测试用例**：
- [ ] JWT生成和验证
- [ ] 配置生成
- [ ] 回调处理
- [ ] 错误处理

---

### ✅ 任务6.2：集成测试 🔴 P0
**负责人**：全栈
**预计时间**：1天

**测试场景**：
- [ ] 文件预览流程
- [ ] 文件编辑流程
- [ ] 文档保存流程
- [ ] 版本创建流程
- [ ] 降级服务切换
- [ ] 错误恢复

---

### ✅ 任务6.3：用户验收测试 🟡 P1
**负责人**：测试/产品
**预计时间**：4小时

**测试清单**：
- [ ] 上传文件后预览
- [ ] 在线编辑文档
- [ ] 保存和版本管理
- [ ] 文书生成后编辑
- [ ] 多用户协作（如支持）
- [ ] 各种文档格式测试
- [ ] 移动端兼容性

---

## 阶段七：部署和上线（1天）

### ✅ 任务7.1：更新环境配置 🔴 P0
**负责人**：运维
**预计时间**：2小时

**任务**：
- [ ] 更新生产环境 `.env`
- [ ] 配置ONLYOFFICE服务器
- [ ] 验证网络连通性
- [ ] 配置防火墙规则

---

### ✅ 任务7.2：数据库迁移 🔴 P0
**负责人**：后端开发
**预计时间**：1小时

**任务**：
- [ ] 检查是否需要数据库变更
- [ ] 创建迁移脚本（如需要）
- [ ] 执行迁移
- [ ] 验证数据完整性

---

### ✅ 任务7.3：部署和验证 🔴 P0
**负责人**：运维
**预计时间**：3小时

**步骤**：
- [ ] 部署后端代码
- [ ] 部署前端代码
- [ ] 重启服务
- [ ] 验证ONLYOFFICE集成
- [ ] 执行冒烟测试
- [ ] 监控日志和错误

---

### ✅ 任务7.4：回滚计划 🔴 P0
**负责人**：运维
**预计时间**：1小时

**准备**：
- [ ] 备份当前代码
- [ ] 备份数据库
- [ ] 准备回滚脚本
- [ ] 文档化回滚步骤

---

## 任务依赖关系

```
阶段一（环境准备）
    ↓
阶段二（后端开发）
    ├─→ 任务2.1 → 任务2.2 → 任务2.3 → 任务2.4
    └─→ 任务2.5
    ↓
阶段三（前端开发）
    ├─→ 任务3.1 → 任务3.2
    └─→ 任务3.3, 3.4, 3.5, 3.6（并行）
    ↓
阶段四（功能增强，可选）
    ↓
阶段五（清理优化）
    ↓
阶段六（测试）
    ├─→ 任务6.1（单元测试）
    ├─→ 任务6.2（集成测试）
    └─→ 任务6.3（验收测试）
    ↓
阶段七（部署上线）
```

## 进度跟踪

| 阶段 | 任务数 | 已完成 | 进行中 | 未开始 | 完成率 |
|------|--------|--------|--------|--------|--------|
| 阶段一 | 3 | 0 | 0 | 3 | 0% |
| 阶段二 | 5 | 0 | 0 | 5 | 0% |
| 阶段三 | 6 | 0 | 0 | 6 | 0% |
| 阶段四 | 3 | 0 | 0 | 3 | 0% |
| 阶段五 | 3 | 0 | 0 | 3 | 0% |
| 阶段六 | 3 | 0 | 0 | 3 | 0% |
| 阶段七 | 4 | 0 | 0 | 4 | 0% |
| **总计** | **27** | **0** | **0** | **27** | **0%** |

## 关键里程碑

- [ ] **里程碑1**：ONLYOFFICE服务验证完成（第1天）
- [ ] **里程碑2**：后端核心服务开发完成（第4天）
- [ ] **里程碑3**：前端组件集成完成（第7天）
- [ ] **里程碑4**：功能测试通过（第10天）
- [ ] **里程碑5**：生产环境部署完成（第11天）

## 风险和问题跟踪

| ID | 风险/问题 | 状态 | 优先级 | 负责人 | 解决方案 |
|----|-----------|------|--------|--------|----------|
| R1 | ONLYOFFICE服务不稳定 | Open | High | 运维 | 保留华为云降级 |
| R2 | JWT配置复杂 | Open | Medium | 后端 | 详细文档和验证 |
| R3 | 前端兼容性问题 | Open | Medium | 前端 | 充分测试 |

## 每日站会检查点

1. 昨天完成了什么？
2. 今天计划做什么？
3. 遇到什么阻碍？
4. 需要什么帮助？

## 验收标准

### 功能验收
- [ ] 所有文档格式可以预览
- [ ] DOCX文件可以在线编辑
- [ ] 编辑后自动保存
- [ ] 版本管理正常工作
- [ ] 降级服务正常切换

### 性能验收
- [ ] 编辑器加载时间 < 3秒
- [ ] 文档保存时间 < 5秒
- [ ] 支持10MB以内的文档

### 安全验收
- [ ] JWT验证正常
- [ ] 权限控制有效
- [ ] 无安全漏洞

## 联系人

- **项目经理**：[姓名]
- **后端负责人**：[姓名]
- **前端负责人**：[姓名]
- **测试负责人**：[姓名]
- **运维负责人**：[姓名]
