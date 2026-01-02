# 本地规则库降级功能 - API 文档

## 概述

本文档描述了本地规则库降级功能提供的所有 API 接口。

---

## 健康监控 API

### 1. 获取健康状态

**端点**: `GET /api/v1/health/status`

**描述**: 获取系统当前健康状态，包括模式、AI 服务状态、连续失败/成功次数等。

**响应示例**:
```json
{
  "mode": "normal",
  "ai_service_healthy": true,
  "consecutive_failures": 0,
  "consecutive_successes": 5,
  "last_check_time": "2026-01-02T10:30:00",
  "last_failure_time": null,
  "estimated_recovery": null
}
```

**字段说明**:
- `mode`: 当前模式（"normal" 或 "fallback"）
- `ai_service_healthy`: AI 服务是否健康
- `consecutive_failures`: 连续失败次数
- `consecutive_successes`: 连续成功次数
- `last_check_time`: 最后检查时间
- `last_failure_time`: 最后失败时间
- `estimated_recovery`: 预计恢复时间（秒）

---

### 2. 获取降级统计

**端点**: `GET /api/v1/health/fallback-stats`

**描述**: 获取降级统计信息，包括降级频率、持续时间等。

**响应示例**:
```json
{
  "total_checks": 120,
  "total_failures": 5,
  "total_fallback_events": 2,
  "total_fallback_duration": 180.5,
  "current_fallback_duration": null,
  "failure_rate": 0.042,
  "uptime_rate": 0.958
}
```

**字段说明**:
- `total_checks`: 总检查次数
- `total_failures`: 总失败次数
- `total_fallback_events`: 总降级事件数
- `total_fallback_duration`: 总降级持续时间（秒）
- `current_fallback_duration`: 当前降级持续时间（秒）
- `failure_rate`: 失败率
- `uptime_rate`: 正常运行率

---

### 3. 简单健康检查

**端点**: `GET /api/v1/health/check`

**描述**: 简单的健康检查端点，用于负载均衡器或监控系统。

**响应示例**:
```json
{
  "status": "healthy",
  "mode": "normal",
  "ai_service_healthy": true
}
```

**字段说明**:
- `status`: 服务状态（"healthy" 或 "degraded"）
- `mode`: 当前模式
- `ai_service_healthy`: AI 服务是否健康

---

## 管理员 API

### 4. 列出所有规则

**端点**: `GET /api/v1/admin/rules/list`

**描述**: 列出所有规则的基本信息，包括启用状态。

**认证**: 需要登录

**响应示例**:
```json
{
  "total_rules": 22,
  "enabled_rules": 20,
  "disabled_rules": 2,
  "rules": [
    {
      "id": "format_001",
      "name": "文号格式检查",
      "category": "format",
      "priority": 100,
      "enabled": true,
      "critical": false,
      "rule_type": "pattern",
      "description": "文号格式不符合规范"
    }
  ]
}
```

---

### 5. 获取规则性能指标

**端点**: `GET /api/v1/admin/rules/performance`

**描述**: 获取每个规则的执行时间统计，标识慢规则。

**认证**: 需要登录

**响应示例**:
```json
{
  "total_validations": 150,
  "total_execution_time": 45.2,
  "average_execution_time": 0.301,
  "rule_metrics": [
    {
      "rule_id": "format_001",
      "rule_name": "文号格式检查",
      "execution_count": 150,
      "total_time": 2.5,
      "average_time": 0.017,
      "max_time": 0.025,
      "min_time": 0.012
    }
  ],
  "slow_rules": []
}
```

**字段说明**:
- `total_validations`: 总验证次数
- `total_execution_time`: 总执行时间（秒）
- `average_execution_time`: 平均执行时间（秒）
- `rule_metrics`: 每个规则的详细指标
- `slow_rules`: 慢规则列表（执行时间 > 500ms）

---

### 6. 获取规则统计信息

**端点**: `GET /api/v1/admin/rules/statistics`

**描述**: 获取规则配置信息、分类统计、性能指标等。

**认证**: 需要登录

**响应示例**:
```json
{
  "config_info": {
    "version": "1.0",
    "total_rules": 22,
    "enabled_rules": 20,
    "last_loaded": "2026-01-02T10:00:00"
  },
  "enabled_rules_count": 20,
  "category_statistics": {
    "format": {
      "count": 7,
      "critical_count": 0
    },
    "content": {
      "count": 8,
      "critical_count": 1
    },
    "compliance": {
      "count": 6,
      "critical_count": 0
    }
  },
  "performance_metrics": {
    "total_validations": 150,
    "average_execution_time": 0.301
  }
}
```

---

### 7. 启用/禁用规则

**端点**: `PUT /api/v1/admin/rules/{rule_id}/toggle`

**描述**: 动态启用或禁用指定规则，无需重启服务。

**认证**: 需要登录

**请求体**:
```json
{
  "enabled": false
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "规则 format_001 已禁用",
  "rule_id": "format_001",
  "enabled": false
}
```

---

### 8. 重载规则配置

**端点**: `POST /api/v1/admin/rules/reload`

**描述**: 手动触发规则配置重载，从配置文件重新加载所有规则。

**认证**: 需要登录

**响应示例**:
```json
{
  "success": true,
  "message": "规则配置已重载",
  "rules_count": 22,
  "enabled_rules_count": 20
}
```

---

## 文档审核 API（降级支持）

### 9. 文档审核（支持降级）

**端点**: `POST /api/v1/documents/review`

**描述**: AI 文档研判，支持自动降级到本地规则引擎。

**认证**: 需要登录

**请求体**:
```json
{
  "file_id": 123
}
```

**响应示例（正常模式）**:
```json
{
  "document_id": 456,
  "errors": [
    {
      "type": "format_error",
      "level": "warning",
      "description": "文号格式不符合规范",
      "suggestion": "文号应符合格式：机关代字〔年份〕序号号"
    }
  ],
  "summary": "发现 1 个问题，1 个警告",
  "fallback_mode": false,
  "fallback_notice": null,
  "estimated_recovery": null
}
```

**响应示例（降级模式）**:
```json
{
  "document_id": 456,
  "errors": [
    {
      "type": "format_error",
      "level": "warning",
      "description": "文号格式不符合规范",
      "suggestion": "文号应符合格式：机关代字〔年份〕序号号"
    }
  ],
  "summary": "发现 1 个问题，1 个警告",
  "fallback_mode": true,
  "fallback_notice": "AI 服务当前不可用，使用本地规则库进行基础校验",
  "estimated_recovery": 60
}
```

**字段说明**:
- `fallback_mode`: 是否使用降级模式
- `fallback_notice`: 降级通知消息
- `estimated_recovery`: 预计恢复时间（秒）

---

## 错误响应

所有 API 在出错时返回标准错误格式：

```json
{
  "detail": "错误描述信息"
}
```

常见错误码：
- `400`: 请求参数错误
- `401`: 未认证
- `403`: 无权限
- `404`: 资源不存在
- `500`: 服务器内部错误
- `503`: 服务不可用

---

## 使用示例

### Python 示例

```python
import httpx

# 获取健康状态
async with httpx.AsyncClient() as client:
    response = await client.get("http://localhost:8000/api/v1/health/status")
    status = response.json()
    print(f"当前模式: {status['mode']}")

# 获取规则列表（需要认证）
headers = {"Authorization": f"Bearer {token}"}
async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8000/api/v1/admin/rules/list",
        headers=headers
    )
    rules = response.json()
    print(f"规则总数: {rules['total_rules']}")

# 禁用规则
async with httpx.AsyncClient() as client:
    response = await client.put(
        "http://localhost:8000/api/v1/admin/rules/format_001/toggle",
        headers=headers,
        json={"enabled": false}
    )
    result = response.json()
    print(result['message'])
```

### JavaScript 示例

```javascript
// 获取健康状态
const response = await fetch('http://localhost:8000/api/v1/health/status');
const status = await response.json();
console.log(`当前模式: ${status.mode}`);

// 获取降级统计
const statsResponse = await fetch('http://localhost:8000/api/v1/health/fallback-stats');
const stats = await statsResponse.json();
console.log(`失败率: ${(stats.failure_rate * 100).toFixed(2)}%`);
```

---

## 配置说明

降级功能相关配置项（在 `.env` 文件中）：

```env
# 降级功能配置
FALLBACK_ENABLED=true                    # 是否启用降级功能
HEALTH_CHECK_INTERVAL=30                 # 健康检查间隔（秒）
AI_HEALTH_TIMEOUT=5                      # AI 健康检查超时时间（秒）
FAILURE_THRESHOLD=3                      # 失败阈值（连续失败次数）
RECOVERY_THRESHOLD=2                     # 恢复阈值（连续成功次数）
LOCAL_VALIDATION_TIMEOUT=3               # 本地验证超时时间（秒）
RULES_CONFIG_PATH=backend/config/validation_rules.json  # 规则配置文件路径
RULES_AUTO_RELOAD=true                   # 是否自动重载规则配置
```

---

## 规则配置文件

规则配置文件位于 `backend/config/validation_rules.json`，支持热重载。

配置文件结构：

```json
{
  "version": "1.0",
  "rules": [
    {
      "id": "规则ID",
      "name": "规则名称",
      "category": "规则类别（format/content/compliance）",
      "priority": 100,
      "enabled": true,
      "critical": false,
      "rule_type": "规则类型（pattern/length/keyword/structure）",
      "parameters": {
        "pattern": "正则表达式",
        "field": "字段名"
      },
      "error_type": "错误类型",
      "error_level": "错误级别（error/warning/info）",
      "description": "错误描述",
      "suggestion": "修改建议"
    }
  ],
  "templates": []
}
```

---

## 监控建议

1. **健康状态监控**: 定期调用 `/api/v1/health/status` 检查系统状态
2. **降级统计监控**: 监控 `failure_rate` 和 `total_fallback_events`
3. **性能监控**: 定期查看 `/api/v1/admin/rules/performance` 识别慢规则
4. **告警设置**: 
   - 降级模式持续超过 5 分钟
   - 失败率超过 10%
   - 发现慢规则（执行时间 > 500ms）

---

**文档版本**: 1.0  
**更新时间**: 2026-01-02  
**维护者**: 开发团队
