# WPS服务配置说明

## 当前状态

✅ **系统已完成WPS集成开发**  
✅ **自动降级机制工作正常**  
⚠️ **需要正确的WPS API端点**

## 问题分析

从调试日志可以看到：
```
[WPS] API URL: https://open.wps.cn/api/v1/office/preview
[WPS] Response status: 404
[WPS] Response text: 404 page not found
```

**原因**: API端点 `https://open.wps.cn/api/v1/office/preview` 不存在，返回404错误。

## 需要的信息

要启用WPS服务，需要从WPS开放平台获取以下信息：

### 1. 正确的API端点
- 预览API: `?` (当前使用的是 `/api/v1/office/preview`，但返回404)
- 编辑API: `?` (当前使用的是 `/api/v1/office/edit`)
- 回调API: `?` (当前使用的是 `/api/v1/wps/callback`)

### 2. API参数格式
需要确认WPS API接受的参数格式：
```json
{
  "app_id": "SX20260103SMMPSL",
  "file_url": "http://...",
  "file_name": "文档.pdf",
  "user_id": "2",
  "permission": "read",
  "timestamp": "1767384755",
  "signature": "..."
}
```

### 3. 签名算法
需要确认签名生成方式是否正确：
```python
# 当前实现
sorted_params = sorted(params.items())
sign_str = "&".join([f"{k}={v}" for k, v in sorted_params])
sign_str = f"{sign_str}&app_secret={self.app_secret}"
signature = hashlib.md5(sign_str.encode()).hexdigest()
```

## 如何获取正确信息

### 方法1: 查看WPS开放平台文档
1. 访问: https://open.wps.cn/docs/
2. 登录你的WPS开放平台账号
3. 查找"文档预览"或"Office在线预览"相关API文档
4. 记录正确的API端点和参数格式

### 方法2: 联系WPS技术支持
1. 在WPS开放平台提交工单
2. 说明需要文档预览API的接口文档
3. 提供你的APP_ID: `SX20260103SMMPSL`

### 方法3: 查看示例代码
如果WPS开放平台提供了示例代码（Python/Java/Node.js），可以参考其中的：
- API端点URL
- 请求参数格式
- 签名生成方式

## 临时方案（当前使用）

在获得正确的WPS API信息之前，系统使用华为云预览服务：

```bash
# backend/.env
WPS_ENABLED=false  # 暂时禁用WPS
```

**优点**:
- ✅ 华为云服务稳定可靠
- ✅ 预览功能正常工作
- ✅ 不影响用户使用

**缺点**:
- ❌ 无法使用WPS的在线编辑功能
- ❌ 无法使用WPS的协同编辑功能

## 启用WPS服务的步骤

一旦获得正确的API信息：

### 1. 更新WPS服务代码
修改 `backend/app/services/wps_service.py`:
```python
# 更新API端点
api_url = f"{self.api_base}/正确的路径"

# 如果参数格式不同，更新参数构建逻辑
params = {
    # 根据实际API要求调整
}

# 如果签名算法不同，更新签名生成逻辑
def _generate_signature(self, params):
    # 根据实际要求调整
```

### 2. 更新配置
```bash
# backend/.env
WPS_ENABLED=true
WPS_API_BASE=正确的API基础URL
```

### 3. 重启服务
```bash
restart-backend.bat
```

### 4. 测试
上传文件并预览，查看日志：
```
[WPS] Response status: 200
[WPS] ✓ Success: https://...
```

## 当前系统架构

```
用户请求预览
    ↓
PreviewServiceSelector
    ↓
尝试WPS服务 (WPS_ENABLED=false，跳过)
    ↓
使用华为云服务 ✓
    ↓
返回预览URL
```

## 相关文件

- `backend/.env` - WPS配置（已禁用）
- `backend/app/services/wps_service.py` - WPS服务实现
- `backend/app/services/preview_service_selector.py` - 预览服务选择器
- `WPS_INTEGRATION_GUIDE.md` - WPS集成指南
- `WPS调试说明.md` - 调试说明

## 总结

✅ **WPS集成代码已完成**  
✅ **自动降级机制已实现**  
✅ **系统功能正常运行**  
⚠️ **等待正确的WPS API端点**

在获得正确的API信息之前，系统使用华为云预览服务，功能完全正常。
