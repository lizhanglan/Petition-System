# WPS预览服务优先级集成完成报告

## 修改时间
2026-01-03

## 修改目标
将项目中所有使用预览服务的地方修改为优先使用WPS服务，失败时自动降级到华为云预览服务。

## 修改内容

### 1. 创建预览服务选择器
**文件**: `backend/app/services/preview_service_selector.py`

创建了统一的预览服务选择器，实现以下功能：

#### 预览URL获取（`get_preview_url`）
- **优先级1**: WPS服务（如果`WPS_ENABLED=true`且配置了`WPS_APP_ID`和`WPS_APP_SECRET`）
- **优先级2**: 华为云预览服务（WPS失败时自动降级）
- **优先级3**: 直接URL（仅PDF文件，浏览器原生支持）
- **优先级4**: 不支持预览（其他格式）

#### 编辑URL获取（`get_edit_url`）
- 仅支持WPS服务
- 需要启用WPS配置才能使用

#### 返回格式
```python
{
    "preview_url": "预览URL",
    "service_type": "wps|huawei|direct|unsupported",
    "file_url": "原始文件URL"
}
```

### 2. 修改文件管理接口
**文件**: `backend/app/api/v1/endpoints/files.py`

#### 修改点1: 文件上传接口（`POST /api/v1/files/upload`）
- 使用`preview_service_selector.get_preview_url()`替代直接调用华为云服务
- 传递用户ID和文件名给WPS服务
- 自动处理服务降级

#### 修改点2: 文件预览接口（`GET /api/v1/files/{file_id}/preview`）
- 使用`preview_service_selector.get_preview_url()`
- 返回`service_type`字段，标识使用的服务类型
- 支持WPS、华为云、直接预览、不支持预览四种状态

#### 修改点3: 导入语句
```python
# 旧代码
from app.services.office_preview_service import office_preview_service

# 新代码
from app.services.preview_service_selector import preview_service_selector
```

### 3. 修改文书管理接口
**文件**: `backend/app/api/v1/endpoints/documents.py`

#### 修改点1: 文书生成接口（`POST /api/v1/documents/generate`）
- 使用`preview_service_selector.get_preview_url()`生成预览URL
- 传递文档标题和用户ID
- 记录使用的服务类型

#### 修改点2: 文书预览接口（`GET /api/v1/documents/{document_id}/preview`）
- 使用`preview_service_selector.get_preview_url()`
- 返回`service_type`字段
- 自动处理服务降级

## 服务降级逻辑

### 降级流程
```
1. 检查WPS_ENABLED配置
   ├─ 是 → 尝试WPS服务
   │   ├─ 成功 → 返回WPS预览URL
   │   └─ 失败 → 继续步骤2
   └─ 否 → 跳到步骤2

2. 尝试华为云预览服务
   ├─ 成功 → 返回华为云预览URL
   └─ 失败 → 继续步骤3

3. 检查文件类型
   ├─ PDF → 返回直接URL（浏览器原生支持）
   └─ 其他 → 返回不支持预览
```

### 日志输出
每个步骤都会输出详细的日志信息：
```
[PreviewSelector] 尝试使用WPS服务...
[PreviewSelector] WPS服务成功: https://...
[PreviewSelector] WPS服务返回空URL，尝试降级...
[PreviewSelector] 使用华为云预览服务...
[PreviewSelector] 华为云服务成功: https://...
[PreviewSelector] 所有预览服务都失败，返回直接URL
```

## 配置说明

### WPS服务配置（`.env`文件）
```bash
# WPS开放平台配置
WPS_APP_ID=your_app_id
WPS_APP_SECRET=your_app_secret
WPS_API_BASE=https://open.wps.cn
WPS_ENABLED=true  # 设置为true启用WPS服务
```

### 华为云服务配置（保持不变）
```bash
# 华为云Office预览服务
OFFICE_HTTP=https://...
OFFICE_API_KEY=...
OFFICE_APP_SECRET=...
OFFICE_MCP_APP_CODE=...
OFFICE_X_APIG_APP_CODE=...
```

## 使用示例

### 前端调用示例
```javascript
// 文件预览
const response = await api.get(`/api/v1/files/${fileId}/preview`);
console.log(response.data);
// {
//   preview_url: "https://...",
//   service_type: "wps",  // 或 "huawei", "direct", "unsupported"
//   file_url: "https://...",
//   file_type: "docx",
//   file_name: "文档.docx"
// }

// 文书预览
const response = await api.get(`/api/v1/documents/${docId}/preview`);
console.log(response.data);
// {
//   preview_url: "https://...",
//   service_type: "wps",
//   file_url: "https://...",
//   document_id: 123
// }
```

### 前端处理建议
```javascript
// 根据service_type显示不同的提示
switch (response.data.service_type) {
  case 'wps':
    // 使用WPS预览，功能最完整
    showPreview(response.data.preview_url);
    break;
  case 'huawei':
    // 使用华为云预览
    showPreview(response.data.preview_url);
    break;
  case 'direct':
    // PDF直接预览
    showPreview(response.data.preview_url);
    break;
  case 'unsupported':
    // 不支持预览，提供下载
    showDownloadButton(response.data.file_url);
    break;
}
```

## 优势

### 1. 服务可靠性
- 双重保障：WPS失败时自动切换到华为云
- 降低单点故障风险
- 提高系统可用性

### 2. 功能完整性
- WPS提供更丰富的预览和编辑功能
- 华为云作为稳定的备选方案
- PDF文件支持浏览器原生预览

### 3. 灵活配置
- 通过`WPS_ENABLED`开关控制是否使用WPS
- 可以根据实际情况选择服务
- 配置简单，易于维护

### 4. 透明降级
- 自动处理服务切换
- 前端无需关心具体使用哪个服务
- 统一的API接口

## 测试建议

### 1. WPS服务测试
```bash
# 启用WPS服务
WPS_ENABLED=true

# 测试文件上传和预览
# 检查日志输出是否显示"WPS服务成功"
```

### 2. 降级测试
```bash
# 方法1: 禁用WPS服务
WPS_ENABLED=false

# 方法2: 使用错误的WPS配置
WPS_APP_ID=invalid
WPS_APP_SECRET=invalid

# 测试文件预览
# 检查日志是否显示降级到华为云服务
```

### 3. 完全失败测试
```bash
# 同时禁用WPS和华为云服务
# 测试PDF文件是否返回直接URL
# 测试Word文件是否返回unsupported
```

## 注意事项

### 1. WPS服务配置
- 需要在WPS开放平台注册应用
- 获取`APP_ID`和`APP_SECRET`
- 配置回调域名（如需编辑功能）

### 2. 文件URL要求
- 文件URL必须是公网可访问的
- MinIO需要配置正确的外网地址
- 确保WPS和华为云都能访问到文件

### 3. 性能考虑
- WPS服务调用有超时时间（30秒）
- 降级会增加响应时间
- 建议监控服务响应时间

### 4. 日志监控
- 关注服务降级频率
- 如果频繁降级，检查WPS配置
- 监控华为云服务可用性

## 后续优化建议

### 1. 缓存机制
- 缓存预览URL，减少API调用
- 设置合理的过期时间
- 考虑使用Redis缓存

### 2. 健康检查
- 定期检查WPS服务可用性
- 自动切换到最优服务
- 记录服务健康状态

### 3. 统计分析
- 记录各服务使用次数
- 分析服务成功率
- 优化服务选择策略

### 4. 前端优化
- 显示当前使用的服务类型
- 提供手动切换服务的选项
- 优化预览加载体验

## 相关文件

### 新增文件
- `backend/app/services/preview_service_selector.py` - 预览服务选择器

### 修改文件
- `backend/app/api/v1/endpoints/files.py` - 文件管理接口
- `backend/app/api/v1/endpoints/documents.py` - 文书管理接口

### 配置文件
- `.env` - 环境配置（需添加WPS配置）
- `backend/app/core/config.py` - 配置类（已包含WPS配置）

### 依赖服务
- `backend/app/services/wps_service.py` - WPS服务实现
- `backend/app/services/office_preview_service.py` - 华为云服务实现

## 总结

本次修改成功实现了预览服务的优先级管理，WPS服务作为首选，华为云服务作为可靠的备选方案。系统现在具有更好的可靠性和灵活性，能够根据实际情况自动选择最优的预览服务。

所有修改都保持了向后兼容性，不影响现有功能。通过简单的配置即可启用或禁用WPS服务，便于测试和部署。
