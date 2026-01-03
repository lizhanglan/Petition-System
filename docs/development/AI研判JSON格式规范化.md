# AI研判JSON格式规范化

**日期**: 2026-01-03  
**问题**: AI返回的是JSON字符串，前端显示为原始JSON格式  
**解决**: 规范AI返回格式，后端正确解析，前端提取纯文本显示

---

## 问题分析

### 原始问题
前端显示的是原始JSON字符串：
```
```json
{
  "errors": [
    {
      "type": "format",
      "description": "文号格式不规范..."
    }
  ]
}
```
```

### 根本原因
1. AI返回的JSON字符串可能包含markdown代码块标记
2. 后端JSON解析不够健壮
3. 前端没有正确提取字段内容

---

## 解决方案

### 1. 规范AI返回格式

**修改文件**: `backend/app/services/deepseek_service.py`

**新的Prompt**:
```python
system_prompt = """你是信访文书审核专家...

**重要：必须严格按照以下JSON格式返回，不要添加任何其他文字：**

{
  "summary": "总体评价文字，简明扼要地说明文档的整体质量和主要问题",
  "errors": [
    {
      "description": "问题的详细描述",
      "suggestion": "具体的修改建议",
      "reference": "相关的法律法规依据（可选）"
    }
  ]
}

如果没有发现问题，errors数组为空即可。"""
```

**字段说明**:
- `summary`: 总体评价（必需）
- `errors`: 问题列表（必需，可为空数组）
  - `description`: 问题描述（必需）
  - `suggestion`: 修改建议（必需）
  - `reference`: 法律依据（可选）

### 2. 清理AI返回内容

**添加清理逻辑**:
```python
if result:
    # 清理可能的markdown代码块标记
    result = result.strip()
    if result.startswith('```json'):
        result = result[7:]
    if result.startswith('```'):
        result = result[3:]
    if result.endswith('```'):
        result = result[:-3]
    result = result.strip()
```

**处理情况**:
- 移除 ` ```json ` 标记
- 移除 ` ``` ` 标记
- 去除首尾空白

### 3. 增强JSON解析

**修改文件**: `backend/app/api/v1/endpoints/documents.py`

**解析逻辑**:
```python
try:
    review_data = json.loads(review_result)
    
    # 确保数据结构正确
    if not isinstance(review_data, dict):
        raise ValueError("AI返回的不是有效的JSON对象")
    
    if "errors" not in review_data:
        review_data["errors"] = []
    
    if "summary" not in review_data:
        review_data["summary"] = "研判完成"
    
    # 确保errors是列表
    if not isinstance(review_data["errors"], list):
        review_data["errors"] = []
    
except json.JSONDecodeError as e:
    print(f"[Review] JSON解析失败: {e}")
    # JSON解析失败，将整个返回作为summary
    review_data = {
        "errors": [],
        "summary": review_result
    }
```

**容错处理**:
1. 验证返回的是字典对象
2. 确保必需字段存在
3. 确保字段类型正确
4. 解析失败时降级处理

### 4. 前端纯文本显示

**修改文件**: `frontend/src/views/Review.vue`

**显示逻辑**:
```vue
<!-- 总体评价 -->
<div class="summary-section">
  <h4>总体评价</h4>
  <div class="summary-content">
    {{ reviewResult.summary }}
  </div>
</div>

<!-- 问题列表 -->
<div class="problems-section">
  <h4>发现 {{ reviewResult.errors.length }} 个问题</h4>
  <div class="problem-list">
    <div v-for="(error, index) in reviewResult.errors" :key="index">
      <div class="problem-number">{{ index + 1 }}.</div>
      <div class="problem-content">
        <p class="problem-text">{{ error.description }}</p>
        <p v-if="error.suggestion" class="suggestion-text">
          <span class="label">建议：</span>{{ error.suggestion }}
        </p>
        <p v-if="error.reference" class="reference-text">
          <span class="label">依据：</span>{{ error.reference }}
        </p>
      </div>
    </div>
  </div>
</div>
```

**提取字段**:
- `reviewResult.summary` - 总体评价
- `error.description` - 问题描述
- `error.suggestion` - 修改建议
- `error.reference` - 法律依据

---

## 数据流程

### 完整流程
```
用户上传文件
    ↓
后端解析文件内容
    ↓
调用DeepSeek API
    ↓
AI返回JSON字符串
    ↓
清理markdown标记
    ↓
解析JSON
    ↓
验证数据结构
    ↓
保存到数据库
    ↓
返回给前端
    ↓
前端提取字段
    ↓
纯文本显示
```

### 数据格式示例

**AI返回（清理前）**:
```
```json
{
  "summary": "文档整体质量良好，发现2个格式问题",
  "errors": [
    {
      "description": "文号格式不规范",
      "suggestion": "请使用标准文号格式",
      "reference": "《党政机关公文格式》7.2.5"
    }
  ]
}
```
```

**清理后**:
```json
{
  "summary": "文档整体质量良好，发现2个格式问题",
  "errors": [
    {
      "description": "文号格式不规范",
      "suggestion": "请使用标准文号格式",
      "reference": "《党政机关公文格式》7.2.5"
    }
  ]
}
```

**前端显示**:
```
总体评价
─────────────────
文档整体质量良好，发现2个格式问题

发现 1 个问题
─────────────────
1. 文号格式不规范
   建议：请使用标准文号格式
   依据：《党政机关公文格式》7.2.5
```

---

## 错误处理

### 1. JSON解析失败
```python
except json.JSONDecodeError as e:
    print(f"[Review] JSON解析失败: {e}")
    review_data = {
        "errors": [],
        "summary": review_result  # 将原始内容作为summary
    }
```

### 2. 数据结构错误
```python
if not isinstance(review_data, dict):
    raise ValueError("AI返回的不是有效的JSON对象")
```

### 3. 字段缺失
```python
if "errors" not in review_data:
    review_data["errors"] = []

if "summary" not in review_data:
    review_data["summary"] = "研判完成"
```

### 4. 类型错误
```python
if not isinstance(review_data["errors"], list):
    review_data["errors"] = []
```

---

## 测试建议

### 1. 正常情况测试
- 上传标准文档
- 验证AI返回正确的JSON
- 验证前端正确显示

### 2. 异常情况测试
- AI返回带markdown标记的JSON
- AI返回格式错误的JSON
- AI返回纯文本（非JSON）
- 网络超时或错误

### 3. 边界情况测试
- 没有发现问题（errors为空）
- 发现大量问题（10+个）
- 问题描述很长
- 缺少可选字段（reference）

---

## 日志输出

### 成功情况
```
[Review] Calling AI service for review...
[DeepSeek] Calling API: https://api.deepseek.com/chat/completions
[DeepSeek] Response status: 200
[DeepSeek] Success: 523 characters
[DeepSeek] Cleaned result: {"summary":"文档整体质量良好...
[Review] Parsing AI result...
[Review] JSON parsed successfully
[Review] Parsed data: summary=文档整体质量良好..., errors_count=2
```

### 失败情况
```
[Review] Calling AI service for review...
[DeepSeek] Response status: 200
[DeepSeek] Success: 523 characters
[Review] Parsing AI result...
[Review] JSON解析失败: Expecting value: line 1 column 1 (char 0)
[Review] AI返回内容: ```json...
[Review] 使用降级方案：将原始内容作为summary
```

---

## 相关文件

- `backend/app/services/deepseek_service.py` - AI服务，规范返回格式
- `backend/app/api/v1/endpoints/documents.py` - 研判接口，解析JSON
- `frontend/src/views/Review.vue` - 前端显示，提取纯文本

---

## 总结

通过规范AI返回格式、增强JSON解析、优化前端显示，成功解决了研判结果显示为原始JSON的问题。现在系统能够：

1. ✅ AI返回标准JSON格式
2. ✅ 自动清理markdown标记
3. ✅ 健壮的JSON解析和验证
4. ✅ 前端纯文本逐步显示
5. ✅ 完善的错误处理和降级

用户现在可以看到清晰、友好的研判结果，而不是原始的JSON字符串。
