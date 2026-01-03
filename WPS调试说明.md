# WPS服务调试说明

## 当前状态
- ✅ WPS配置已添加到 `backend/.env`
- ✅ WPS服务已启用（WPS_ENABLED=true）
- ⚠️ WPS服务返回空URL，需要调试

## 已完成的修改
更新了 `backend/app/services/wps_service.py`，添加了详细的调试日志。

## 下一步操作

### 1. 重启后端服务
使用以下任一方法：
- 双击运行 `restart-backend.bat`
- 或在后端窗口按 `Ctrl+C`，然后重新运行 `start.bat`

### 2. 测试预览功能
上传一个文件并点击预览，查看后端日志。

### 3. 查看详细日志
现在会输出以下详细信息：
```
[WPS] ========== 开始请求WPS预览服务 ==========
[WPS] APP_ID: SX20260103SMMPSL
[WPS] API_BASE: https://open.wps.cn
[WPS] File Name: 文档.pdf
[WPS] File URL: http://124.70.74.202:9000/...
[WPS] User ID: 2
[WPS] Permission: read
[WPS] Request params: {...}
[WPS] Signature: ...
[WPS] API URL: https://open.wps.cn/api/v1/office/preview
[WPS] Sending POST request...
[WPS] Response status: 200
[WPS] Response body: {...}
[WPS] ========== WPS预览服务请求结束 ==========
```

## 可能的问题

### 问题1: WPS API端点不正确
**症状**: HTTP 404错误
**解决**: 需要查看WPS开放平台文档，确认正确的API端点

### 问题2: 签名验证失败
**症状**: 返回签名错误
**解决**: 检查APP_ID和APP_SECRET是否正确

### 问题3: 文件URL无法访问
**症状**: WPS无法下载文件
**解决**: 确保MinIO的URL是公网可访问的

### 问题4: WPS服务未开通
**症状**: 返回权限错误
**解决**: 在WPS开放平台确认服务已开通

## 联系WPS技术支持

如果问题持续，可能需要：
1. 查看WPS开放平台文档：https://open.wps.cn/docs/
2. 联系WPS技术支持
3. 确认API端点和参数格式

## 临时方案

在WPS服务调试期间，系统会自动降级到华为云预览服务，不影响正常使用。
