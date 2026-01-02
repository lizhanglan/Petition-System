# DeepSeek API 调用失败排查指南

## 🐛 问题现象

### 错误日志
```
[Review] Starting review for file: xxx.pdf (type: pdf)
[Review] File downloaded: 1028514 bytes
[FileParser] PDF parsed successfully: 6 pages, 1187 characters
[Review] File parsed: 1187 characters
API call attempt 1 failed: 
API call attempt 2 failed: 
API call attempt 3 failed: 
```

### 问题特征
- 文件解析成功
- AI API 调用失败
- 重试 3 次都失败
- 错误信息为空

---

## 🔍 排查步骤

### 步骤 1：测试 API 连接

运行测试脚本：
```bash
cd backend
python test_deepseek.py
```

**预期结果**：
```
✅ 测试通过！DeepSeek API 连接正常
```

**如果失败**：
- 检查网络连接
- 检查 API Key 是否有效
- 检查防火墙设置

---

### 步骤 2：检查配置

查看 `.env` 文件：
```bash
# DeepSeek API 配置
DEEPSEEK_API_KEY=sk-xxx...
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

**检查项**：
- [x] API Key 是否正确
- [x] API Base URL 是否正确
- [x] Model 名称是否正确

---

### 步骤 3：检查超时设置

查看 `backend/app/core/config.py`：
```python
API_TIMEOUT: int = 120  # 120 秒
```

**检查项**：
- [x] 超时时间是否足够（建议 120 秒）
- [x] 网络延迟是否过高

---

### 步骤 4：查看详细错误日志

修改后的代码会打印详细的错误信息：
```python
print(f"API call attempt {attempt + 1} failed: [{error_type}] {error_msg}")
traceback.print_exc()
```

**查看后端日志**，寻找：
- 错误类型（TimeoutException, ConnectError, etc.）
- 错误详情
- 堆栈跟踪

---

## 🔧 常见问题和解决方案

### 问题 1：API Key 无效

**症状**：
```
API call failed: 401 - {"error": "Invalid API key"}
```

**解决方案**：
1. 检查 `.env` 文件中的 API Key
2. 登录 DeepSeek 官网验证 API Key
3. 重新生成 API Key

---

### 问题 2：网络超时

**症状**：
```
API call timeout after 120 seconds
```

**解决方案**：
1. 检查网络连接
2. 增加超时时间
3. 检查防火墙设置
4. 尝试使用代理

---

### 问题 3：请求内容过长

**症状**：
```
API call failed: 400 - {"error": "Request too large"}
```

**解决方案**：
1. 限制文件大小
2. 截断文件内容
3. 分块处理

**代码示例**：
```python
# 限制内容长度
max_length = 10000  # 10000 字符
if len(content) > max_length:
    content = content[:max_length] + "\n\n[内容过长，已截断]"
```

---

### 问题 4：返回格式错误

**症状**：
```
KeyError: 'choices'
```

**解决方案**：
1. 检查 API 返回格式
2. 添加错误处理
3. 打印完整响应

**代码示例**：
```python
if response.status_code == 200:
    result = response.json()
    print(f"API Response: {result}")  # 打印完整响应
    
    if "choices" in result and len(result["choices"]) > 0:
        content = result["choices"][0]["message"]["content"]
        return content
    else:
        raise Exception(f"Unexpected response format: {result}")
```

---

### 问题 5：并发限制

**症状**：
```
API call failed: 429 - {"error": "Rate limit exceeded"}
```

**解决方案**：
1. 增加重试延迟
2. 减少并发请求
3. 升级 API 套餐

---

## 📊 调试技巧

### 1. 启用详细日志

在 `deepseek_service.py` 中添加：
```python
print(f"[DeepSeek] Request payload: {payload}")
print(f"[DeepSeek] Response: {response.text}")
```

### 2. 使用 Postman 测试

直接测试 DeepSeek API：
```
POST https://api.deepseek.com/chat/completions
Headers:
  Authorization: Bearer sk-xxx...
  Content-Type: application/json
Body:
{
  "model": "deepseek-chat",
  "messages": [
    {"role": "user", "content": "测试"}
  ]
}
```

### 3. 检查网络连接

```bash
# 测试 DNS 解析
nslookup api.deepseek.com

# 测试连接
curl -I https://api.deepseek.com

# 测试 API
curl -X POST https://api.deepseek.com/chat/completions \
  -H "Authorization: Bearer sk-xxx..." \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"test"}]}'
```

---

## 🎯 最佳实践

### 1. 错误处理

```python
try:
    result = await deepseek_service.review_document(content)
    if not result:
        # 提供友好的错误提示
        raise HTTPException(
            status_code=500,
            detail="AI 服务暂时不可用，请稍后重试"
        )
except Exception as e:
    # 记录详细错误
    print(f"Review error: {str(e)}")
    traceback.print_exc()
    raise
```

### 2. 内容长度限制

```python
# 限制内容长度，避免超时
MAX_CONTENT_LENGTH = 10000

if len(content) > MAX_CONTENT_LENGTH:
    content = content[:MAX_CONTENT_LENGTH]
    print(f"[Review] Content truncated to {MAX_CONTENT_LENGTH} characters")
```

### 3. 重试策略

```python
# 配置合理的重试策略
API_RETRY_TIMES = 3
API_RETRY_DELAYS = "2000,5000,10000"  # 2s, 5s, 10s
```

### 4. 超时设置

```python
# 根据内容长度动态调整超时
base_timeout = 30
timeout = base_timeout + (len(content) // 1000) * 5  # 每 1000 字符增加 5 秒
```

---

## 📝 相关文件

- `backend/test_deepseek.py` - API 连接测试脚本
- `backend/app/services/deepseek_service.py` - DeepSeek 服务实现
- `backend/app/core/config.py` - 配置文件
- `.env` - 环境变量配置

---

## ✅ 验收标准

- [x] API 连接测试通过
- [x] 配置正确无误
- [x] 错误日志详细清晰
- [x] 重试机制正常工作
- [x] 超时设置合理
- [x] 错误提示友好

---

**更新时间**：2026-01-02  
**状态**：排查中
