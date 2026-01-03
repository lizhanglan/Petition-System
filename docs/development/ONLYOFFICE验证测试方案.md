# ONLYOFFICE集成验证测试方案

## 验证结果 ✅

### 服务可用性验证

**测试时间**：2026-01-03

#### 1. 健康检查
```bash
curl http://101.37.24.171:9090/healthcheck
```
**结果**：✅ 成功
- 状态码：200
- 返回：`true`
- 服务状态：正常运行

#### 2. API脚本访问
```bash
curl http://101.37.24.171:9090/web-apps/apps/api/documents/api.js
```
**结果**：✅ 成功
- 状态码：200
- 内容类型：application/javascript
- 文件大小：64KB
- ONLYOFFICE版本：**9.2.1 (build:8)**

#### 3. JWT验证状态
**配置**：❌ JWT验证已关闭
- 无需JWT token
- 简化集成流程
- 降低实现复杂度

### 结论
✅ **ONLYOFFICE服务完全可用，可以开始集成开发**

---

## 简化方案（无JWT版本）

由于ONLYOFFICE服务器已关闭JWT验证，我们可以简化集成方案：

### 移除的内容
- ❌ JWT密钥生成
- ❌ JWT token生成逻辑
- ❌ JWT token验证逻辑
- ❌ PyJWT依赖

### 保留的内容
- ✅ 编辑器配置生成
- ✅ 文档key生成（用于缓存）
- ✅ 回调处理
- ✅ 文件下载接口
- ✅ 权限控制（后端验证）

### 优势
1. **实现更简单**：减少30%代码量
2. **开发更快**：预计节省1-2天
3. **维护更容易**：减少配置项
4. **调试更方便**：减少错误点

---

## 最小验证测试（MVP）

### 测试目标
验证ONLYOFFICE能否正常预览和编辑文档

### 测试步骤

#### 步骤1：创建测试HTML页面（5分钟）

创建文件：`test_onlyoffice.html`

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ONLYOFFICE测试</title>
</head>
<body>
    <h1>ONLYOFFICE集成测试</h1>
    <div id="placeholder" style="width: 100%; height: 600px;"></div>
    
    <script src="http://101.37.24.171:9090/web-apps/apps/api/documents/api.js"></script>
    <script>
        // 测试配置（无JWT）
        var config = {
            "document": {
                "fileType": "docx",
                "key": "test_document_key_001",
                "title": "测试文档.docx",
                "url": "https://file-examples.com/storage/fe1fce8e0f66f8c5e7b1f8f/2017/02/file-sample_100kB.docx",
                "permissions": {
                    "edit": false,  // 先测试只读模式
                    "download": true,
                    "print": true
                }
            },
            "documentType": "word",
            "editorConfig": {
                "mode": "view",
                "lang": "zh-CN",
                "user": {
                    "id": "test_user_001",
                    "name": "测试用户"
                },
                "customization": {
                    "autosave": true,
                    "forcesave": false,
                    "comments": false,
                    "chat": false
                }
            },
            "events": {
                "onDocumentReady": function() {
                    console.log("✅ 文档加载成功");
                    alert("✅ ONLYOFFICE集成测试成功！文档已加载。");
                },
                "onError": function(event) {
                    console.error("❌ 错误:", event);
                    alert("❌ 错误: " + JSON.stringify(event));
                }
            }
        };
        
        // 初始化编辑器
        var docEditor = new DocsAPI.DocEditor("placeholder", config);
    </script>
</body>
</html>
```

#### 步骤2：在浏览器中打开测试页面

1. 将上述HTML保存为文件
2. 在浏览器中打开
3. 观察是否显示文档

**预期结果**：
- ✅ 编辑器加载成功
- ✅ 显示测试文档内容
- ✅ 弹出"集成测试成功"提示

#### 步骤3：测试编辑模式（可选）

修改配置中的：
```javascript
"permissions": {
    "edit": true  // 改为true
},
"editorConfig": {
    "mode": "edit"  // 改为edit
}
```

**预期结果**：
- ✅ 可以编辑文档
- ✅ 工具栏显示编辑按钮

---

## 集成验证测试

### 测试1：后端配置生成

**目标**：验证后端能正确生成ONLYOFFICE配置

**测试代码**：
```python
# 在Python环境中运行
from datetime import datetime
import hashlib

def generate_document_key(file_id: int, updated_at: datetime) -> str:
    """生成文档唯一key"""
    key_string = f"{file_id}_{updated_at.timestamp()}"
    return hashlib.md5(key_string.encode()).hexdigest()

def get_editor_config(file_id: int, file_url: str, file_name: str):
    """生成编辑器配置（无JWT版本）"""
    document_key = generate_document_key(file_id, datetime.now())
    
    config = {
        "document": {
            "fileType": "docx",
            "key": document_key,
            "title": file_name,
            "url": file_url,
            "permissions": {
                "edit": True,
                "download": True,
                "print": True
            }
        },
        "documentType": "word",
        "editorConfig": {
            "mode": "edit",
            "lang": "zh-CN",
            "callbackUrl": f"http://your-backend/api/v1/onlyoffice/callback?fileId={file_id}",
            "user": {
                "id": "user_123",
                "name": "测试用户"
            }
        }
    }
    
    return config

# 测试
config = get_editor_config(
    file_id=1,
    file_url="http://example.com/test.docx",
    file_name="测试文档.docx"
)

print("✅ 配置生成成功:")
import json
print(json.dumps(config, indent=2, ensure_ascii=False))
```

**预期输出**：
```json
{
  "document": {
    "fileType": "docx",
    "key": "生成的MD5哈希",
    "title": "测试文档.docx",
    "url": "http://example.com/test.docx",
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
    "callbackUrl": "http://your-backend/api/v1/onlyoffice/callback?fileId=1",
    "user": {
      "id": "user_123",
      "name": "测试用户"
    }
  }
}
```

### 测试2：文件访问验证

**目标**：验证ONLYOFFICE能访问MinIO中的文件

**前提条件**：
- MinIO服务正常运行
- 文件URL可公网访问

**测试步骤**：
1. 上传一个测试文档到MinIO
2. 获取文件的公网URL
3. 在浏览器中访问该URL，确认可下载
4. 使用该URL配置ONLYOFFICE

**验证命令**：
```bash
# 测试MinIO文件URL是否可访问
curl -I http://124.70.74.202:9000/petition-files/test.docx
```

**预期结果**：
- ✅ 返回200状态码
- ✅ Content-Type正确
- ✅ 文件可下载

### 测试3：回调处理验证

**目标**：验证ONLYOFFICE保存回调能正常工作

**测试回调数据**：
```json
{
  "status": 2,
  "url": "http://101.37.24.171:9090/cache/files/data/conv_xxx/output.docx",
  "key": "document_key_001",
  "users": ["user_123"]
}
```

**回调状态说明**：
- 0：文档未找到
- 1：文档正在编辑
- 2：文档准备保存 ✅
- 3：文档保存错误
- 4：文档关闭无变化
- 6：文档正在编辑，但保存当前状态 ✅
- 7：强制保存错误

**测试代码**：
```python
def handle_callback(callback_data: dict):
    """处理回调（简化版本）"""
    status = callback_data.get('status')
    
    print(f"收到回调，状态: {status}")
    
    if status in [2, 6]:
        download_url = callback_data.get('url')
        print(f"✅ 文档准备保存，下载URL: {download_url}")
        return {"error": 0}
    
    return {"error": 0}

# 测试
callback_data = {
    "status": 2,
    "url": "http://example.com/output.docx",
    "key": "test_key"
}

result = handle_callback(callback_data)
print(f"回调处理结果: {result}")
```

---

## 完整集成测试流程

### 阶段1：基础功能测试

#### 测试用例1.1：文档预览
- [ ] 上传DOCX文件
- [ ] 点击预览
- [ ] ONLYOFFICE编辑器加载
- [ ] 文档内容正确显示
- [ ] 可以滚动浏览

#### 测试用例1.2：文档编辑
- [ ] 点击"编辑"按钮
- [ ] 编辑器切换到编辑模式
- [ ] 可以修改文本
- [ ] 可以修改格式
- [ ] 工具栏功能正常

#### 测试用例1.3：文档保存
- [ ] 编辑文档内容
- [ ] 点击保存
- [ ] 回调接口被调用
- [ ] 文件成功保存到MinIO
- [ ] 文件大小更新
- [ ] 可以重新预览看到修改

### 阶段2：集成功能测试

#### 测试用例2.1：文件上传后预览
- [ ] 在"文件管理"上传文件
- [ ] 点击预览按钮
- [ ] ONLYOFFICE正确显示

#### 测试用例2.2：文书生成后预览
- [ ] 生成一份文书
- [ ] 右侧预览区显示ONLYOFFICE
- [ ] 可以在线编辑
- [ ] 保存后更新文档

#### 测试用例2.3：文书管理编辑
- [ ] 在文书列表点击"编辑"
- [ ] ONLYOFFICE编辑器打开
- [ ] 编辑并保存
- [ ] 创建新版本

### 阶段3：兼容性测试

#### 测试用例3.1：文档格式
- [ ] DOCX文件
- [ ] DOC文件
- [ ] PDF文件（只读）
- [ ] XLSX文件
- [ ] PPTX文件

#### 测试用例3.2：浏览器兼容
- [ ] Chrome
- [ ] Firefox
- [ ] Edge
- [ ] Safari

#### 测试用例3.3：文件大小
- [ ] 小文件（< 1MB）
- [ ] 中等文件（1-5MB）
- [ ] 大文件（5-10MB）

### 阶段4：性能测试

#### 测试用例4.1：加载速度
- [ ] 编辑器初始化时间 < 3秒
- [ ] 文档加载时间 < 5秒
- [ ] 保存响应时间 < 3秒

#### 测试用例4.2：并发测试
- [ ] 5个用户同时预览
- [ ] 3个用户同时编辑不同文档
- [ ] 系统响应正常

---

## 验证检查清单

### 环境检查
- [x] ONLYOFFICE服务可访问（101.37.24.171:9090）
- [x] ONLYOFFICE版本：9.2.1
- [x] JWT验证已关闭
- [ ] MinIO服务正常
- [ ] MinIO文件URL可从ONLYOFFICE访问
- [ ] 后端服务可从ONLYOFFICE访问（回调）

### 配置检查
- [ ] ONLYOFFICE_ENABLED=true
- [ ] ONLYOFFICE_SERVER_URL正确
- [ ] ONLYOFFICE_JWT_ENABLED=false
- [ ] ONLYOFFICE_CALLBACK_URL正确
- [ ] MinIO URL配置正确

### 功能检查
- [ ] 配置生成正确
- [ ] 文档key生成正确
- [ ] 文件URL可访问
- [ ] 回调接口正常
- [ ] 权限控制有效

### 安全检查
- [ ] 用户权限验证
- [ ] 文件访问控制
- [ ] 回调来源验证（可选）
- [ ] 错误处理完善

---

## 问题排查指南

### 问题1：编辑器显示"下载错误"

**可能原因**：
- ONLYOFFICE无法访问文件URL
- MinIO URL配置错误
- 网络防火墙阻止

**排查步骤**：
1. 在ONLYOFFICE服务器上测试：
   ```bash
   curl -I http://your-minio-url/file.docx
   ```
2. 检查MinIO是否使用公网IP
3. 检查防火墙规则

**解决方案**：
- 使用公网可访问的MinIO URL
- 配置防火墙允许ONLYOFFICE访问MinIO

### 问题2：编辑器无法加载

**可能原因**：
- ONLYOFFICE服务不可用
- API脚本加载失败
- 浏览器跨域问题

**排查步骤**：
1. 检查ONLYOFFICE服务：
   ```bash
   curl http://101.37.24.171:9090/healthcheck
   ```
2. 检查浏览器控制台错误
3. 检查网络请求

**解决方案**：
- 确认ONLYOFFICE服务正常
- 检查CORS配置
- 使用HTTPS（生产环境）

### 问题3：保存回调失败

**可能原因**：
- 回调URL不可访问
- 回调接口错误
- 网络问题

**排查步骤**：
1. 在ONLYOFFICE服务器上测试回调URL：
   ```bash
   curl -X POST http://your-backend/api/v1/onlyoffice/callback
   ```
2. 检查后端日志
3. 检查防火墙规则

**解决方案**：
- 使用公网可访问的回调URL
- 确保回调接口正确实现
- 配置防火墙规则

### 问题4：文档key冲突

**可能原因**：
- 文档key生成逻辑错误
- 缓存问题

**排查步骤**：
1. 检查key生成逻辑
2. 确保每次修改后key变化
3. 清除浏览器缓存

**解决方案**：
- 使用文件ID + 更新时间生成key
- 每次保存后更新updated_at字段

---

## 下一步行动

### 立即执行（今天）
1. ✅ 验证ONLYOFFICE服务（已完成）
2. [ ] 运行HTML测试页面
3. [ ] 验证MinIO文件URL可访问
4. [ ] 测试配置生成逻辑

### 明天开始
1. [ ] 实现后端服务类（无JWT版本）
2. [ ] 创建API端点
3. [ ] 测试基础功能

### 本周完成
1. [ ] 前端组件开发
2. [ ] 页面集成
3. [ ] 完整测试
4. [ ] 部署验证

---

## 验证报告模板

### 测试日期
2026-01-03

### 测试人员
[姓名]

### 测试环境
- ONLYOFFICE版本：9.2.1
- 后端：FastAPI
- 前端：Vue 3
- 浏览器：Chrome/Firefox/Edge

### 测试结果

| 测试项 | 状态 | 备注 |
|--------|------|------|
| ONLYOFFICE服务可用 | ✅ 通过 | 版本9.2.1 |
| API脚本可访问 | ✅ 通过 | 64KB |
| JWT验证状态 | ✅ 已关闭 | 简化集成 |
| HTML测试页面 | ⏳ 待测试 | - |
| MinIO文件访问 | ⏳ 待测试 | - |
| 配置生成 | ⏳ 待测试 | - |
| 回调处理 | ⏳ 待测试 | - |

### 问题记录
无

### 结论
✅ **ONLYOFFICE服务验证通过，可以开始集成开发**

### 建议
1. 使用简化方案（无JWT）
2. 先实现MVP验证可行性
3. 逐步完善功能

---

**文档版本**：1.0  
**最后更新**：2026-01-03  
**状态**：验证通过 ✅
