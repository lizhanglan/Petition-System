# Design Document: Local Rules Fallback System

## Overview

The Local Rules Fallback System provides a reliable backup mechanism for document validation when the DeepSeek AI service is unavailable. The system implements automatic health monitoring, intelligent fallback switching, and a rule-based validation engine that can perform basic document checks without external dependencies.

### Key Design Goals

1. **High Availability**: Ensure document validation remains available even when AI services fail
2. **Transparent Fallback**: Automatically switch between AI and local validation without user intervention
3. **Performance**: Local validation should complete within 3 seconds for typical documents
4. **Maintainability**: Rules should be easy to configure and update without code changes
5. **Observability**: Provide clear visibility into system health and fallback events

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer                                │
│  /api/v1/documents/review (with fallback support)           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Health Monitor Service                          │
│  - Periodic health checks (30s interval)                     │
│  - Failure tracking and threshold detection                  │
│  - Automatic mode switching                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│  AI Service      │    │ Local Rules      │
│  (Primary)       │    │ Engine           │
│                  │    │ (Fallback)       │
│ - DeepSeek API   │    │ - Rule Loader    │
│ - Full analysis  │    │ - Rule Executor  │
│ - 30s timeout    │    │ - Basic checks   │
└──────────────────┘    └──────────────────┘
                               │
                               ▼
                     ┌──────────────────┐
                     │  Rule Repository │
                     │  (JSON/YAML)     │
                     │                  │
                     │ - Format rules   │
                     │ - Content rules  │
                     │ - Compliance     │
                     └──────────────────┘
```

### Component Interactions

1. **Request Flow (Normal Mode)**:
   - User submits document review request
   - Health Monitor checks AI service status
   - If healthy, route to AI Service
   - Return AI analysis results

2. **Request Flow (Fallback Mode)**:
   - User submits document review request
   - Health Monitor detects AI service unavailable
   - Route to Local Rules Engine
   - Execute validation rules
   - Return basic validation results with fallback notice

3. **Health Monitoring**:
   - Background task runs every 30 seconds
   - Performs lightweight health check on AI service
   - Tracks consecutive failures
   - Switches mode when threshold exceeded (3 failures)
   - Switches back after 2 consecutive successes

## Components and Interfaces

### 1. Health Monitor Service

**File**: `backend/app/services/health_monitor_service.py`

**Responsibilities**:
- Monitor AI service health status
- Track failure counts and recovery
- Manage system mode (normal/fallback)
- Provide health status API

**Interface**:
```python
class HealthMonitorService:
    async def start_monitoring(self) -> None
    async def stop_monitoring(self) -> None
    async def check_ai_health(self) -> bool
    def is_fallback_mode(self) -> bool
    def get_health_status(self) -> dict
    def get_estimated_recovery_time(self) -> Optional[int]
```

**State Management**:
```python
{
    "mode": "normal" | "fallback",
    "ai_service_healthy": bool,
    "consecutive_failures": int,
    "consecutive_successes": int,
    "last_check_time": datetime,
    "last_failure_time": Optional[datetime],
    "total_fallback_events": int,
    "current_fallback_duration": Optional[int]
}
```

### 2. Local Rules Engine

**File**: `backend/app/services/local_rules_engine.py`

**Responsibilities**:
- Load and manage validation rules
- Execute rules against documents
- Collect and format validation results
- Track performance metrics

**Interface**:
```python
class LocalRulesEngine:
    def __init__(self, rules_config_path: str)
    async def load_rules(self) -> None
    async def reload_rules(self) -> None
    async def validate_document(self, content: str, metadata: dict) -> ValidationResult
    def get_performance_metrics(self) -> dict
    def get_rule_statistics(self) -> dict
```

**Rule Definition Format** (JSON):
```json
{
  "rules": [
    {
      "id": "format_001",
      "name": "检查文号格式",
      "category": "format",
      "priority": 100,
      "enabled": true,
      "pattern": "^[A-Z]+〔\\d{4}〕\\d+号$",
      "error_type": "format_error",
      "error_level": "warning",
      "description": "文号格式不正确",
      "suggestion": "文号应符合格式：机关代字〔年份〕序号",
      "critical": false
    },
    {
      "id": "content_001",
      "name": "检查文书长度",
      "category": "content",
      "priority": 90,
      "enabled": true,
      "min_length": 100,
      "max_length": 50000,
      "error_type": "content_error",
      "error_level": "error",
      "description": "文书长度超出范围",
      "suggestion": "文书长度应在100-50000字之间",
      "critical": false
    }
  ]
}
```

### 3. Rule Executor

**File**: `backend/app/services/rule_executor.py`

**Responsibilities**:
- Execute individual rules
- Support different rule types (regex, length, keyword, etc.)
- Handle rule chaining
- Collect execution metrics

**Interface**:
```python
class RuleExecutor:
    async def execute_rule(self, rule: Rule, content: str, context: dict) -> RuleResult
    async def execute_rules(self, rules: List[Rule], content: str) -> List[RuleResult]
    def get_execution_time(self, rule_id: str) -> float
```

**Rule Types**:
1. **Pattern Rules**: Regex-based validation
2. **Length Rules**: Min/max length checks
3. **Keyword Rules**: Required/prohibited keywords
4. **Structure Rules**: Document structure validation
5. **Custom Rules**: Python function-based rules

### 4. Fallback-Aware Document Service

**File**: `backend/app/api/v1/endpoints/documents.py` (modified)

**Changes**:
```python
@router.post("/review", response_model=DocumentReviewResponse)
async def review_document(
    request: DocumentReviewRequest,
    req: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if in fallback mode
    if health_monitor.is_fallback_mode():
        # Use local rules engine
        result = await local_rules_engine.validate_document(content, metadata)
        result.fallback_mode = True
        result.fallback_notice = "当前使用本地规则库进行基础校验，AI 服务暂时不可用"
        result.estimated_recovery = health_monitor.get_estimated_recovery_time()
    else:
        # Try AI service with fallback
        try:
            result = await deepseek_service.review_document(content)
        except Exception as e:
            # Immediate fallback on error
            logger.warning(f"AI service failed, using fallback: {e}")
            result = await local_rules_engine.validate_document(content, metadata)
            result.fallback_mode = True
            result.fallback_notice = "AI 服务调用失败，已切换到本地规则库"
    
    return result
```

### 5. Configuration Manager

**File**: `backend/app/core/rules_config.py`

**Responsibilities**:
- Load rules configuration from file
- Watch for configuration changes
- Validate configuration syntax
- Provide rule templates

**Interface**:
```python
class RulesConfigManager:
    def __init__(self, config_path: str)
    async def load_config(self) -> dict
    async def reload_config(self) -> bool
    def validate_config(self, config: dict) -> Tuple[bool, Optional[str]]
    def get_rule_templates(self) -> List[dict]
    async def start_watching(self) -> None
```

## Data Models

### ValidationResult

```python
class ValidationResult(BaseModel):
    success: bool
    errors: List[ValidationError]
    summary: str
    fallback_mode: bool = False
    fallback_notice: Optional[str] = None
    estimated_recovery: Optional[int] = None
    execution_time: float
    rules_executed: int
```

### ValidationError

```python
class ValidationError(BaseModel):
    type: str  # format_error, content_error, compliance_error
    level: str  # error, warning, info
    position: Optional[dict]  # {line: int, column: int, field: str}
    description: str
    suggestion: Optional[str]
    reference: Optional[str]  # Rule ID or regulation reference
```

### Rule

```python
class Rule(BaseModel):
    id: str
    name: str
    category: str  # format, content, compliance
    priority: int  # 1-100, higher = earlier execution
    enabled: bool
    critical: bool  # If true, stop on error
    rule_type: str  # pattern, length, keyword, structure, custom
    parameters: dict  # Rule-specific parameters
    error_type: str
    error_level: str
    description: str
    suggestion: Optional[str]
```

### HealthStatus

```python
class HealthStatus(BaseModel):
    mode: str  # normal, fallback
    ai_service_healthy: bool
    consecutive_failures: int
    last_check_time: datetime
    last_failure_time: Optional[datetime]
    estimated_recovery: Optional[int]
    fallback_statistics: dict
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Rule Storage Format Consistency
*For any* validation rule stored in the system, the rule data should be serializable to and deserializable from JSON/YAML format without data loss.
**Validates: Requirements 1.1**

### Property 2: Rule Validation Rejection
*For any* rule definition with invalid syntax or structure, the system should reject it and not add it to the active rule set.
**Validates: Requirements 1.2**

### Property 3: Rule State Toggle
*For any* rule in the system, when disabled, it should not be executed during document validation.
**Validates: Requirements 1.4**

### Property 4: Rule Execution Order
*For any* set of rules with different priorities, they should execute in descending priority order (highest priority first).
**Validates: Requirements 1.5, 5.1**

### Property 5: Timeout Detection
*For any* AI service call that exceeds 5 seconds, the system should mark the service as unhealthy.
**Validates: Requirements 2.2**

### Property 6: Failure Counter Increment
*For any* AI service error response, the consecutive failure counter should increment by exactly 1.
**Validates: Requirements 2.3**

### Property 7: Fallback Activation Threshold
*For any* sequence of 3 consecutive AI service failures, the system should activate fallback mode.
**Validates: Requirements 2.4**

### Property 8: Recovery Deactivation
*For any* sequence of 2 consecutive successful health checks while in fallback mode, the system should deactivate fallback mode.
**Validates: Requirements 2.5**

### Property 9: AI Service Priority
*For any* document review request when not in fallback mode, the system should attempt AI service first before considering fallback.
**Validates: Requirements 3.1**

### Property 10: Automatic Fallback Switch
*For any* document review request when AI service is unavailable, the system should automatically use the local rules engine.
**Validates: Requirements 3.2**

### Property 11: Fallback Event Logging
*For any* fallback event, the system should create a log entry with timestamp and reason.
**Validates: Requirements 3.3**

### Property 12: Fallback Mode Notice
*For any* validation result generated in fallback mode, the response should include a fallback_mode flag set to true and a notice message.
**Validates: Requirements 3.4, 6.1, 6.2**

### Property 13: Local Validation Performance
*For any* document up to 10,000 characters, local rules engine validation should complete within 3 seconds.
**Validates: Requirements 3.5, 5.5**

### Property 14: Format Error Detection
*For any* document with missing required fields, incorrect date formats, or invalid structure, the local rules engine should detect and report these errors.
**Validates: Requirements 4.1**

### Property 15: Content Error Detection
*For any* document with excessive length, prohibited keywords, or missing signatures, the local rules engine should detect and report these errors.
**Validates: Requirements 4.2**

### Property 16: Compliance Error Detection
*For any* document with missing case numbers, incorrect classification levels, or invalid recipient information, the local rules engine should detect and report these errors.
**Validates: Requirements 4.3**

### Property 17: Error Report Completeness
*For any* detected error, the validation result should include error type, location, description, and suggested correction.
**Validates: Requirements 4.4**

### Property 18: Critical Error Early Termination
*For any* document validation where a critical error is detected, rule execution should stop immediately and return the critical error.
**Validates: Requirements 5.3**

### Property 19: Non-Critical Error Aggregation
*For any* document validation with multiple non-critical errors, all errors should be collected and returned together.
**Validates: Requirements 5.4**

### Property 20: Fallback Request Logging
*For any* user request processed in fallback mode, an audit log entry should be created.
**Validates: Requirements 6.4**

### Property 21: Configuration Reload
*For any* valid configuration file modification, the system should reload rules without requiring a restart.
**Validates: Requirements 7.2**

### Property 22: Invalid Configuration Handling
*For any* invalid configuration file, the system should log an error and continue using the previous valid configuration.
**Validates: Requirements 7.4**

### Property 23: Rule Execution Time Tracking
*For any* rule execution, the system should record the execution time in milliseconds.
**Validates: Requirements 8.1**

### Property 24: Validation Count Tracking
*For any* document validation performed by the local rules engine, the total validation counter should increment by 1.
**Validates: Requirements 8.2**

### Property 25: Average Time Calculation
*For any* set of validation executions, the calculated average time should equal the sum of execution times divided by the count.
**Validates: Requirements 8.3**

### Property 26: Slow Rule Identification
*For any* rule with execution time exceeding 500ms, the system should flag it as slow-performing.
**Validates: Requirements 8.4**

## Error Handling

### AI Service Errors

1. **Connection Errors**: Immediate fallback to local rules
2. **Timeout Errors**: Count as failure, trigger fallback after threshold
3. **API Errors (4xx/5xx)**: Count as failure, log details
4. **Rate Limit Errors**: Temporary fallback, retry after cooldown

### Local Rules Engine Errors

1. **Rule Execution Errors**: Skip rule, log error, continue with other rules
2. **Configuration Errors**: Use previous valid configuration, alert admin
3. **Performance Issues**: Log slow rules, continue execution

### Fallback Mode Errors

1. **Both Systems Fail**: Return error response with clear message
2. **Partial Rule Failures**: Return partial results with warnings
3. **Configuration Missing**: Use built-in default rules

## Testing Strategy

### Unit Tests

1. **Rule Validation**: Test rule syntax validation with valid/invalid rules
2. **Rule Execution**: Test individual rule types with various inputs
3. **Health Monitoring**: Test state transitions and threshold detection
4. **Configuration Loading**: Test config parsing and validation

### Property-Based Tests

All correctness properties listed above should be implemented as property-based tests using a Python PBT library (e.g., Hypothesis). Each test should:
- Run minimum 100 iterations
- Generate random valid inputs
- Verify the property holds for all inputs
- Reference the design property in a comment

Example test structure:
```python
# Feature: local-rules-fallback, Property 4: Rule Execution Order
@given(st.lists(st.builds(Rule), min_size=2, max_size=10))
async def test_rule_execution_order(rules):
    """For any set of rules with different priorities, 
    they should execute in descending priority order"""
    # Assign random priorities
    for i, rule in enumerate(rules):
        rule.priority = random.randint(1, 100)
    
    # Execute rules
    executor = RuleExecutor()
    execution_order = await executor.execute_rules(rules, "test content")
    
    # Verify order
    priorities = [r.priority for r in execution_order]
    assert priorities == sorted(priorities, reverse=True)
```

### Integration Tests

1. **End-to-End Fallback**: Simulate AI failure, verify fallback activation
2. **Recovery Flow**: Simulate AI recovery, verify mode switch back
3. **Performance**: Validate 3-second response time requirement
4. **Concurrent Requests**: Test fallback under load

### Performance Tests

1. **Rule Execution Time**: Measure time for 20+ rules on 10k char document
2. **Health Check Overhead**: Measure impact of monitoring on system
3. **Configuration Reload**: Measure reload time for large rule sets

## Configuration

### Rules Configuration File

**Location**: `backend/config/validation_rules.json`

**Structure**:
```json
{
  "version": "1.0",
  "rules": [
    {
      "id": "format_001",
      "name": "文号格式检查",
      "category": "format",
      "priority": 100,
      "enabled": true,
      "critical": false,
      "rule_type": "pattern",
      "parameters": {
        "pattern": "^[A-Z]+〔\\d{4}〕\\d+号$",
        "field": "document_number"
      },
      "error_type": "format_error",
      "error_level": "warning",
      "description": "文号格式不符合规范",
      "suggestion": "文号应符合格式：机关代字〔年份〕序号号"
    }
  ],
  "templates": [
    {
      "name": "日期格式检查",
      "rule_type": "pattern",
      "parameters": {
        "pattern": "\\d{4}年\\d{1,2}月\\d{1,2}日"
      }
    }
  ]
}
```

### System Configuration

**File**: `backend/app/core/config.py` (additions)

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Fallback Configuration
    FALLBACK_ENABLED: bool = True
    HEALTH_CHECK_INTERVAL: int = 30  # seconds
    AI_TIMEOUT: int = 5  # seconds
    FAILURE_THRESHOLD: int = 3  # consecutive failures
    RECOVERY_THRESHOLD: int = 2  # consecutive successes
    LOCAL_VALIDATION_TIMEOUT: int = 3  # seconds
    RULES_CONFIG_PATH: str = "config/validation_rules.json"
    RULES_AUTO_RELOAD: bool = True
```

## Deployment Considerations

### Initialization

1. Load rules configuration at startup
2. Start health monitoring background task
3. Perform initial AI service health check
4. Initialize performance metrics storage

### Monitoring

1. **Health Status Endpoint**: `/api/v1/health/status`
2. **Fallback Statistics**: `/api/v1/health/fallback-stats`
3. **Rule Performance**: `/api/v1/admin/rules/performance`

### Logging

1. **Fallback Events**: Log level WARNING
2. **Health Check Failures**: Log level INFO
3. **Rule Execution Errors**: Log level ERROR
4. **Configuration Reloads**: Log level INFO

### Metrics

1. **Fallback Frequency**: Count of fallback activations per hour
2. **Fallback Duration**: Average time spent in fallback mode
3. **Rule Performance**: P50, P95, P99 execution times per rule
4. **Validation Success Rate**: Percentage of successful validations

## Security Considerations

1. **Rule Injection**: Validate all rule configurations to prevent code injection
2. **Resource Limits**: Limit rule execution time and memory usage
3. **Access Control**: Restrict rule configuration access to admins only
4. **Audit Logging**: Log all configuration changes and fallback events

## Future Enhancements

1. **Machine Learning**: Learn from AI results to improve local rules
2. **Rule Suggestions**: Automatically suggest new rules based on common errors
3. **A/B Testing**: Compare AI vs local validation accuracy
4. **Distributed Rules**: Support loading rules from multiple sources
5. **Rule Marketplace**: Share and download community-contributed rules
