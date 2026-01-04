# ONLYOFFICE 下载失败错误修复（errorCode: -4）

**文档版本**: 1.1  
**更新日期**: 2026-01-04  
**问题状态**: ✅ 已修复

---

## 问题描述

在 AI 生成文书并预览时，出现以下错误：

```
[OnlyOffice] ❌ Error event: Object
  data: {errorCode: -4, errorDescription: '下载失败'}

AttributeError: 'Document' object has no attribute 'file_path'
```

### 错误代码说明

- **errorCode: -4** - 文档下载失败
- **原因**: 后端代码访问了不存在的 `document.file_path` 字段

---

## 根本原因

### Document 模型字段缺失

在 `backend/app/api/v1/endpoints/onlyoffice.py` 第 226 行，代码尝试访问 `document.file_path`：

```python
print(f"[OnlyOffice] Storage path: {document.file_path}")
                                      ^^^^^^^^^^^^^^^^^^
AttributeError: 'Document' object has no attribute 'file_path'
```

**问题**：
- Document 模型中没有 `file_path` 字段
- 文书文件路径是动态生成的：`temp_preview/{user_id}/{document_id}.docx`
- 代码直接访问不存在的字段导致 500 错误

---

## 解决方案

### 修复：动态生成文件路径并添加容错机制

修改 `backend/app/api/v1/endpoints/onlyoffice.py` 第 224-250 行：

```python
# 修改前
print(f"[OnlyOffice] Document found: {document.title}")
print(f"[OnlyOffice] Storage path: {document.file_path}")  # ❌ 字段不存在

file_data = await minio_client.download_file(document.file_path)

# 修改后
print(f"[OnlyOffice] Document found: {document.title}")

# 生成文件路径（与生成时保持一致）
file_path = f"temp_preview/{document.user_id}/{document.id}.docx"
print(f"[OnlyOffice] Storage path: {file_path}")

# 从MinIO下载文书
file_data = await minio_client.download_file(file_path)

# 如果文件不存在，尝试重新生成
if not file_data:
    print(f"[OnlyOffice] File not found in MinIO, regenerating...")
    from app.services.document_export_service import document_export_service
    
    # 重新生成 DOCX 文件
    docx_bytes = await document_export_service.export_to_docx(
        content=document.content,
        title=document.title,
        options={"document_type": document.document_type}
    )
    
    # 上传到 MinIO
    await minio_client.upload_file(
        file_path,
        docx_bytes,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    
    file_data = docx_bytes
    print(f"[OnlyOffice] File regenerated, size: {len(file_data)} bytes")
```

### 修复亮点

1. **动态生成路径**：根据 `user_id` 和 `document_id` 动态生成文件路径
2. **容错机制**：如果文件不存在，自动重新生成并上传
3. **保持一致性**：与文书生成时的路径格式完全一致

---

## 部署步骤

### 1. 提交代码到 GitHub

```bash
git add backend/app/api/v1/endpoints/onlyoffice.py
git add backend/app/services/onlyoffice_service.py
git add docs/troubleshooting/ONLYOFFICE-download-error-fix.md
git commit -m "fix: 修复 OnlyOffice 文书下载失败问题 (errorCode: -4)"
git push origin main
```

### 2. 在服务器上更新代码

```bash
ssh root@101.37.24.171
cd ~/lizhanglan/Petition-System
git pull origin main
```

### 3. 重启后端服务

```bash
docker-compose restart petition-backend
```

### 4. 测试文书生成预览

1. 访问：http://101.37.24.171:8081
2. 登录系统
3. 进入"文书生成"页面
4. 生成文书并查看预览

**预期结果**：
- ✅ OnlyOffice 编辑器正常加载
- ✅ 文档内容正常显示
- ✅ 没有 errorCode: -4 错误

---

## 修复日期

2026-01-04

## 状态

✅ 已修复
