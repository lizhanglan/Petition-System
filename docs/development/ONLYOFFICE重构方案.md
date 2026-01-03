# ONLYOFFICE文档预览与编辑功能重构方案

## 项目背景

当前系统使用WPS和华为云服务进行文档预览，但存在以下问题：
- WPS服务API端点返回404，不稳定
- 华为云服务仅支持预览，不支持在线编辑
- 缺乏统一的文档协作编辑能力
- 预览服务切换逻辑复杂

## 解决方案

使用ONLYOFFICE社区版替代现有预览服务，实现统一的文档预览和在线编辑功能。

**ONLYOFFICE服务信息**：
- 部署方式：Docker部署在阿里云
- 公网地址：`http://101.37.24.171:9090`
- 版本：社区版（Community Edition）

## 技术架构

### ONLYOFFICE Document Server API

ONLYOFFICE提供以下核心功能：
1. **文档预览**：支持DOCX、XLSX、PPTX、PDF等格式
2. **在线编辑**：支持多人协作编辑
3. **版本控制**：支持文档版本管理
4. **回调机制**：编辑完成后自动保存到服务器

### 集成方式

```
用户浏览器 <---> FastAPI后端 <---> MinIO存储
                    |
                    v
              ONLYOFFICE Server
              (101.37.24.171:9090)
```

## 重构任务流程

### 阶段一：基础服务集成（优先级：高）

#### 任务1.1：创建ONLYOFFICE服务类
**文件**：`backend/app/services/onlyoffice_service.py`

**功能**：
- 生成ONLYOFFICE配置JSON
- 生成文档访问token（JWT）
- 处理文档保存回调
- 支持预览和编辑模式

**关键方法**：
```python
class OnlyOfficeService:
    async def get_editor_config(file_url, file_name, user_info, mode='view')
    async def handle_callback(callback_data)
    async def generate_token(payload)
    async def verify_token(token)
```

#### 任务1.2：更新配置文件
**文件**：`backend/app/core/config.py`

**新增配置**：
```python
# ONLYOFFICE配置
ONLYOFFICE_ENABLED: bool = True
ONLYOFFICE_SERVER_URL: str = "http://101.37.24.171:9090"
ONLYOFFICE_JWT_SECRET: str = ""  # JWT密钥
ONLYOFFICE_JWT_ENABLED: bool = True  # 是否启用JWT验证
```

**环境变量**（`.env`）：
```bash
ONLYOFFICE_ENABLED=true
ONLYOFFICE_SERVER_URL=http://101.37.24.171:9090
ONLYOFFICE_JWT_SECRET=your_secret_key_here
ONLYOFFICE_JWT_ENABLED=true
```

#### 任务1.3：创建API端点
**文件**：`backend/app/api/v1/endpoints/onlyoffice.py`

**端点**：
- `POST /api/v1/onlyoffice/config` - 获取编辑器配置
- `POST /api/v1/onlyoffice/callback` - 处理保存回调
- `GET /api/v1/onlyoffice/download/{file_id}` - 下载文件（供ONLYOFFICE访问）

### 阶段二：重构预览服务选择器（优先级：高）

#### 任务2.1：更新预览服务选择器
**文件**：`backend/app/services/preview_service_selector.py`

**修改策略**：
```
优先级顺序：
1. ONLYOFFICE（主要服务）
2. 华为云（降级服务，仅预览）
3. 直接URL（PDF文件）
```

**关键改动**：
```python
class PreviewServiceSelector:
    async def get_preview_url(self, file_url, file_name, user_id, permission='read'):
        # 1. 优先使用ONLYOFFICE
        if settings.ONLYOFFICE_ENABLED:
            return await onlyoffice_service.get_editor_config(
                file_url, file_name, user_id, mode='view'
            )
        
        # 2. 降级到华为云
        # 3. 直接URL
    
    async def get_edit_url(self, file_url, file_name, user_id, user_name):
        # 仅使用ONLYOFFICE
        if settings.ONLYOFFICE_ENABLED:
            return await onlyoffice_service.get_editor_config(
                file_url, file_name, user_id, mode='edit'
            )
```

### 阶段三：前端集成（优先级：高）

#### 任务3.1：创建ONLYOFFICE编辑器组件
**文件**：`frontend/src/components/OnlyOfficeEditor.vue`

**功能**：
- 嵌入ONLYOFFICE编辑器iframe
- 处理编辑器事件（保存、关闭等）
- 支持预览和编辑模式切换

**组件接口**：
```vue
<OnlyOfficeEditor
  :file-id="fileId"
  :mode="'edit'"  // 'view' or 'edit'
  @save="handleSave"
  @close="handleClose"
/>
```

#### 任务3.2：更新文件预览页面
**文件**：`frontend/src/views/Files.vue`

**改动**：
- 使用ONLYOFFICE编辑器替代现有iframe
- 添加"在线编辑"按钮
- 处理编辑完成后的刷新

#### 任务3.3：更新文书生成预览
**文件**：`frontend/src/views/Generate.vue`

**改动**：
- 右侧预览区使用ONLYOFFICE编辑器
- 支持实时编辑生成的文书
- 编辑后自动保存到文档库

#### 任务3.4：更新文书管理页面
**文件**：`frontend/src/views/Documents.vue`

**改动**：
- 添加"在线编辑"功能
- 使用ONLYOFFICE编辑器打开文书
- 支持版本对比（利用ONLYOFFICE的版本功能）

### 阶段四：文档编辑功能增强（优先级：中）

#### 任务4.1：实现协作编辑
**功能**：
- 多用户同时编辑同一文档
- 实时显示其他用户的光标位置
- 编辑冲突检测和解决

#### 任务4.2：版本管理集成
**文件**：`backend/app/services/version_service.py`

**功能**：
- 每次保存自动创建版本
- 版本对比（利用ONLYOFFICE的对比功能）
- 版本回滚

#### 任务4.3：评论和批注
**功能**：
- 支持文档内评论
- AI研判结果作为批注显示在文档中
- 评论历史记录

### 阶段五：移除旧服务（优先级：低）

#### 任务5.1：移除WPS服务
**文件**：
- 删除 `backend/app/services/wps_service.py`
- 删除 `backend/app/api/v1/endpoints/wps.py`
- 从配置中移除WPS相关配置

#### 任务5.2：保留华为云服务作为降级
**文件**：`backend/app/services/office_preview_service.py`

**保留原因**：
- 作为ONLYOFFICE不可用时的降级方案
- 仅用于只读预览

#### 任务5.3：清理前端代码
- 移除WPS相关组件和API调用
- 统一使用ONLYOFFICE编辑器组件

## 详细实现步骤

### 步骤1：验证ONLYOFFICE服务可用性

```bash
# 测试ONLYOFFICE服务是否正常
curl http://101.37.24.171:9090/healthcheck

# 预期返回：true
```

### 步骤2：生成JWT密钥

```python
import secrets
jwt_secret = secrets.token_urlsafe(32)
print(f"ONLYOFFICE_JWT_SECRET={jwt_secret}")
```

### 步骤3：配置ONLYOFFICE服务器

如果ONLYOFFICE服务器需要配置JWT：

```bash
# 在ONLYOFFICE服务器的docker-compose.yml中添加
environment:
  - JWT_ENABLED=true
  - JWT_SECRET=your_secret_key_here
```

### 步骤4：实现核心服务类

参考ONLYOFFICE官方文档：
- API文档：https://api.onlyoffice.com/editors/basic
- 配置示例：https://api.onlyoffice.com/editors/config/

### 步骤5：前端集成

使用ONLYOFFICE提供的JavaScript API：
```html
<script src="http://101.37.24.171:9090/web-apps/apps/api/documents/api.js"></script>
```

## 数据流程

### 预览流程
```
1. 用户点击"预览"
2. 前端请求 /api/v1/onlyoffice/config
3. 后端生成配置JSON（包含文件URL、用户信息、token）
4. 前端使用配置初始化ONLYOFFICE编辑器
5. ONLYOFFICE从MinIO下载文件并显示
```

### 编辑流程
```
1. 用户点击"编辑"
2. 前端请求 /api/v1/onlyoffice/config (mode=edit)
3. 后端生成编辑配置
4. 用户在ONLYOFFICE中编辑
5. 用户保存，ONLYOFFICE调用callback接口
6. 后端从ONLYOFFICE下载编辑后的文件
7. 后端保存到MinIO并创建新版本
8. 返回成功响应
```

## 配置示例

### ONLYOFFICE编辑器配置JSON
```json
{
  "document": {
    "fileType": "docx",
    "key": "unique_document_key",
    "title": "文档标题.docx",
    "url": "http://your-backend/api/v1/onlyoffice/download/123"
  },
  "documentType": "word",
  "editorConfig": {
    "mode": "edit",
    "lang": "zh-CN",
    "callbackUrl": "http://your-backend/api/v1/onlyoffice/callback",
    "user": {
      "id": "user_123",
      "name": "张三"
    },
    "customization": {
      "autosave": true,
      "forcesave": true
    }
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

## 安全考虑

1. **JWT验证**：所有请求必须包含有效的JWT token
2. **权限控制**：验证用户是否有权限访问/编辑文档
3. **文件隔离**：确保用户只能访问自己的文件
4. **回调验证**：验证callback请求来自ONLYOFFICE服务器
5. **HTTPS**：生产环境必须使用HTTPS

## 性能优化

1. **文档缓存**：缓存频繁访问的文档配置
2. **CDN加速**：ONLYOFFICE静态资源使用CDN
3. **异步处理**：文档保存使用异步任务
4. **连接池**：复用HTTP连接

## 测试计划

### 单元测试
- ONLYOFFICE服务类方法测试
- JWT生成和验证测试
- 回调处理逻辑测试

### 集成测试
- 文档预览流程测试
- 文档编辑和保存流程测试
- 多用户协作测试
- 降级服务切换测试

### 用户验收测试
- 文件上传后预览
- 在线编辑文档
- 文书生成后编辑
- 版本管理功能

## 风险评估

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| ONLYOFFICE服务不稳定 | 高 | 中 | 保留华为云作为降级方案 |
| JWT配置错误 | 高 | 低 | 详细的配置文档和验证脚本 |
| 文件保存失败 | 高 | 低 | 实现重试机制和错误恢复 |
| 性能问题 | 中 | 中 | 实施缓存和优化策略 |
| 兼容性问题 | 中 | 低 | 充分测试各种文档格式 |

## 时间估算

| 阶段 | 任务 | 预计时间 |
|------|------|----------|
| 阶段一 | 基础服务集成 | 2-3天 |
| 阶段二 | 重构预览服务 | 1天 |
| 阶段三 | 前端集成 | 3-4天 |
| 阶段四 | 功能增强 | 2-3天 |
| 阶段五 | 清理旧代码 | 1天 |
| 测试 | 全面测试 | 2天 |
| **总计** | | **11-16天** |

## 交付物

1. **代码**：
   - ONLYOFFICE服务类
   - API端点
   - 前端编辑器组件
   - 更新的预览服务选择器

2. **文档**：
   - API接口文档
   - 部署配置指南
   - 用户使用手册
   - 故障排查指南

3. **测试**：
   - 单元测试代码
   - 集成测试用例
   - 测试报告

## 后续优化

1. **移动端适配**：ONLYOFFICE移动端编辑器集成
2. **离线编辑**：支持离线编辑和同步
3. **模板库**：集成ONLYOFFICE模板功能
4. **插件开发**：开发自定义ONLYOFFICE插件
5. **AI集成**：在编辑器中集成AI写作助手

## 参考资料

- [ONLYOFFICE API文档](https://api.onlyoffice.com/)
- [ONLYOFFICE集成示例](https://github.com/ONLYOFFICE/document-server-integration)
- [JWT规范](https://jwt.io/)
- [FastAPI文档](https://fastapi.tiangolo.com/)
