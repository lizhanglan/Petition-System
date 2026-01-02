# Word 文档预览问题分析与解决方案

## 问题已解决！✅

### 最终诊断结果（2026-01-02 15:44）

**华为云服务返回的错误：**
```json
{
  "request_ok": false,
  "view_url": null,
  "error_msg": "请传递文件下载地址：file_url",
  "return_code": 20,
  "return_code_descrip": "参数校验错误，请检查参数传递"
}
```

**根本原因：**
- 华为云 API 期望的参数名是 `file_url`
- 我们的代码发送的是 `url`
- 参数名不匹配导致 API 返回错误

**修复方案：**
```python
# backend/app/services/office_preview_service.py
payload = {
    "file_url": file_url,  # 改为 file_url（之前是 url）
    "app_code": self.mcp_app_code
}
```

同时修复返回字段：
```python
# 华为云返回的字段是 view_url 而不是 preview_url
preview_url = result.get("view_url") or result.get("preview_url")
```

---

## 完整问题分析历史

### 问题描述

**现象：**
- PDF 文件可以正常预览和研判
- Word 文档（.doc/.docx）无法预览，点击预览时会自动下载文件

### 问题排查过程

#### 1. 初步怀疑：MinIO URL 的 Content-Disposition

**假设：** MinIO 生成的 URL 导致浏览器下载而不是预览

**实施：** 添加 `response-content-disposition=inline` 参数

**结果：** ✅ URL 包含了 inline 参数，但问题依然存在

#### 2. 发现：浏览器无法直接预览 Word

**事实：** 浏览器的 `<iframe>` 只能直接预览 PDF、图片等格式，Word 文档需要转换

**结论：** 必须依赖华为云预览服务将 Word 转换为可预览格式

#### 3. 最终发现：API 参数错误

**通过日志发现：**
```
[Preview Service] Response body: {
  "error_msg": "请传递文件下载地址：file_url"
}
```

**根本原因：** 参数名错误（`url` vs `file_url`）

## 已实施的修复

### 1. 修复华为云 API 调用 ✅

```python
# backend/app/services/office_preview_service.py
payload = {
    "file_url": file_url,  # 正确的参数名
    "app_code": self.mcp_app_code
}

# 正确的返回字段
preview_url = result.get("view_url") or result.get("preview_url")
```

### 2. MinIO URL 优化 ✅

```python
# backend/app/core/minio_client.py
def get_file_url(self, file_name: str, expires: int = 3600, inline: bool = True):
    response_headers = {}
    if inline:
        response_headers['response-content-disposition'] = 'inline'
    return self.client.presigned_get_object(...)
```

### 3. 增强日志输出 ✅

```python
print(f"[Preview Service] Requesting preview for URL: {file_url}")
print(f"[Preview Service] Response status: {response.status_code}")
print(f"[Preview Service] Response body: {response.text}")
```

### 4. 降级方案 ✅

```python
# 如果华为云服务失败，使用 Microsoft Office Online Viewer
if not preview_url:
    preview_url = f"https://view.officeapps.live.com/op/embed.aspx?src={file_url}"
```

### 5. 前端错误处理 ✅

```vue
<div v-if="previewUrl && !previewError">
  <iframe :src="previewUrl" ... />
</div>
<div v-else class="preview-error">
  <el-empty description="无法预览该文件">
    <el-button @click="handleDownloadCurrent">下载文件</el-button>
  </el-empty>
</div>
```

### 6. 添加下载接口 ✅

```python
@router.get("/{file_id}/download")
async def download_file_by_id(...):
    download_url = minio_client.get_file_url(file.storage_path, inline=False)
    return RedirectResponse(url=download_url)
```

## 测试验证

### 测试步骤

1. ✅ 重启后端服务
2. ✅ 上传 Word 文档
3. ✅ 点击预览按钮
4. ✅ 查看后端日志确认 API 调用成功
5. ✅ 确认 Word 文档能在 iframe 中预览

### 预期结果

- Word 文档通过华为云服务转换后正常预览
- PDF 文档继续正常工作
- 预览失败时有友好的错误提示和下载选项
- 后端日志清晰显示预览服务的调用过程

## 技术要点总结

### 华为云 Office 预览服务 API

**请求格式：**
```json
{
  "file_url": "文件的公网可访问 URL",
  "app_code": "应用代码"
}
```

**响应格式：**
```json
{
  "request_ok": true,
  "view_url": "预览页面 URL",
  "return_code": 0
}
```

**关键字段：**
- 请求参数：`file_url`（不是 `url`）
- 返回字段：`view_url`（不是 `preview_url`）

### MinIO 预签名 URL

**Content-Disposition 控制：**
- `inline`：浏览器尝试在线预览
- `attachment`：浏览器直接下载

**实现方式：**
```python
response_headers = {
    'response-content-disposition': 'inline'  # 或 'attachment'
}
```

### 浏览器预览限制

**原生支持：**
- PDF、图片、纯文本、HTML、视频、音频

**需要转换：**
- Word（.doc/.docx）
- Excel（.xls/.xlsx）
- PowerPoint（.ppt/.pptx）

## 经验教训

1. **仔细阅读 API 文档** - 参数名和返回字段要准确
2. **添加详细日志** - 帮助快速定位问题
3. **实施降级方案** - 提高系统可用性
4. **前端友好提示** - 改善用户体验

## 相关文件

- `backend/app/services/office_preview_service.py` - 华为云预览服务
- `backend/app/core/minio_client.py` - MinIO 客户端
- `backend/app/api/v1/endpoints/files.py` - 文件接口
- `frontend/src/views/Files.vue` - 文件管理页面
- `frontend/src/views/Review.vue` - 研判页面
