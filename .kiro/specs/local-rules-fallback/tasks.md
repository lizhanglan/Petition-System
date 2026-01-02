# Implementation Plan: Local Rules Fallback System

## Overview

本实现计划将本地规则库降级功能分解为一系列增量开发任务。每个任务都是独立的、可测试的步骤，最终组合成完整的降级系统。实现将采用 Python，与现有的 FastAPI 后端集成。

## Tasks

- [x] 1. 创建规则数据模型和配置结构
  - 定义 Rule、ValidationResult、ValidationError 数据模型
  - 创建规则配置文件结构（JSON schema）
  - 实现配置文件验证逻辑
  - _Requirements: 1.1, 1.2_

- [ ]* 1.1 为规则数据模型编写属性测试
  - **Property 1: Rule Storage Format Consistency**
  - **Validates: Requirements 1.1**

- [ ] 2. 实现规则配置管理器
  - [x] 2.1 创建 RulesConfigManager 类
    - 实现配置文件加载功能
    - 实现配置验证逻辑
    - 添加规则模板支持
    - _Requirements: 7.1, 7.3, 7.5_

  - [ ]* 2.2 为配置验证编写属性测试
    - **Property 2: Rule Validation Rejection**
    - **Validates: Requirements 1.2**

  - [x] 2.3 实现配置热重载功能
    - 使用 watchdog 监控配置文件变化
    - 实现配置重载逻辑
    - 添加错误恢复机制（使用上一个有效配置）
    - _Requirements: 7.2, 7.4_

  - [ ]* 2.4 为配置热重载编写属性测试
    - **Property 21: Configuration Reload**
    - **Property 22: Invalid Configuration Handling**
    - **Validates: Requirements 7.2, 7.4**

- [ ] 3. 实现规则执行器
  - [x] 3.1 创建 RuleExecutor 类
    - 实现基础规则执行框架
    - 支持不同规则类型（pattern, length, keyword）
    - 添加执行时间跟踪
    - _Requirements: 5.1, 8.1_

  - [ ]* 3.2 为规则执行顺序编写属性测试
    - **Property 4: Rule Execution Order**
    - **Validates: Requirements 1.5, 5.1**

  - [ ] 3.3 实现规则类型处理器
    - Pattern 规则：正则表达式匹配
    - Length 规则：长度范围检查
    - Keyword 规则：关键词检测
    - Structure 规则：文档结构验证
    - _Requirements: 4.1, 4.2, 4.3_

  - [ ]* 3.4 为错误检测编写属性测试
    - **Property 14: Format Error Detection**
    - **Property 15: Content Error Detection**
    - **Property 16: Compliance Error Detection**
    - **Validates: Requirements 4.1, 4.2, 4.3**

  - [ ] 3.5 实现关键错误早停机制
    - 检测关键错误标志
    - 立即停止执行并返回
    - _Requirements: 5.3_

  - [ ]* 3.6 为关键错误处理编写属性测试
    - **Property 18: Critical Error Early Termination**
    - **Validates: Requirements 5.3**

  - [ ] 3.7 实现非关键错误聚合
    - 收集所有非关键错误
    - 统一返回错误列表
    - _Requirements: 5.4_

  - [ ]* 3.8 为错误聚合编写属性测试
    - **Property 19: Non-Critical Error Aggregation**
    - **Validates: Requirements 5.4**

- [ ] 4. 实现本地规则引擎
  - [x] 4.1 创建 LocalRulesEngine 类
    - 集成 RulesConfigManager 和 RuleExecutor
    - 实现文档验证主流程
    - 添加性能监控
    - _Requirements: 3.5, 5.5_

  - [ ]* 4.2 为验证性能编写属性测试
    - **Property 13: Local Validation Performance**
    - **Validates: Requirements 3.5, 5.5**

  - [ ] 4.3 实现错误报告格式化
    - 确保包含错误类型、位置、描述、建议
    - 格式化为 ValidationResult
    - _Requirements: 4.4_

  - [ ]* 4.4 为错误报告编写属性测试
    - **Property 17: Error Report Completeness**
    - **Validates: Requirements 4.4**

  - [ ] 4.5 实现性能指标收集
    - 记录每个规则的执行时间
    - 跟踪验证总数
    - 计算平均验证时间
    - 识别慢规则（>500ms）
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [ ]* 4.6 为性能指标编写属性测试
    - **Property 23: Rule Execution Time Tracking**
    - **Property 24: Validation Count Tracking**
    - **Property 25: Average Time Calculation**
    - **Property 26: Slow Rule Identification**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4**

- [ ] 5. 检查点 - 确保规则引擎功能完整
  - 确保所有规则类型正常工作
  - 验证性能指标收集正确
  - 确保所有测试通过
  - 如有问题请询问用户

- [ ] 6. 实现健康监控服务
  - [x] 6.1 创建 HealthMonitorService 类
    - 实现 AI 服务健康检查
    - 实现状态管理（normal/fallback）
    - 跟踪连续失败和成功次数
    - _Requirements: 2.1, 2.2, 2.3_

  - [ ]* 6.2 为健康检查编写属性测试
    - **Property 5: Timeout Detection**
    - **Property 6: Failure Counter Increment**
    - **Validates: Requirements 2.2, 2.3**

  - [ ] 6.3 实现降级模式切换逻辑
    - 失败阈值检测（3次失败）
    - 恢复阈值检测（2次成功）
    - 模式切换和状态更新
    - _Requirements: 2.4, 2.5_

  - [ ]* 6.4 为模式切换编写属性测试
    - **Property 7: Fallback Activation Threshold**
    - **Property 8: Recovery Deactivation**
    - **Validates: Requirements 2.4, 2.5**

  - [ ] 6.5 实现后台健康检查任务
    - 使用 asyncio 创建后台任务
    - 30秒间隔执行健康检查
    - 优雅启动和停止
    - _Requirements: 2.1_

  - [ ] 6.6 实现恢复时间估算
    - 基于历史数据估算恢复时间
    - 提供给用户参考
    - _Requirements: 6.3_

- [ ] 7. 集成降级功能到文档审核接口
  - [x] 7.1 修改 documents.py 审核接口
    - 检查健康监控状态
    - 根据状态选择 AI 或本地引擎
    - 添加降级通知到响应
    - _Requirements: 3.1, 3.2, 3.4_

  - [ ]* 7.2 为请求路由编写属性测试
    - **Property 9: AI Service Priority**
    - **Property 10: Automatic Fallback Switch**
    - **Validates: Requirements 3.1, 3.2**

  - [ ] 7.3 实现降级事件日志记录
    - 记录所有降级事件
    - 包含时间戳和原因
    - 记录降级模式下的用户请求
    - _Requirements: 3.3, 6.4_

  - [ ]* 7.4 为降级日志编写属性测试
    - **Property 11: Fallback Event Logging**
    - **Property 20: Fallback Request Logging**
    - **Validates: Requirements 3.3, 6.4**

  - [ ] 7.5 实现降级模式响应格式
    - 添加 fallback_mode 标志
    - 添加 fallback_notice 消息
    - 添加 estimated_recovery 时间
    - _Requirements: 6.1, 6.2, 6.3_

  - [ ]* 7.6 为降级响应格式编写属性测试
    - **Property 12: Fallback Mode Notice**
    - **Validates: Requirements 3.4, 6.1, 6.2**

- [ ] 8. 创建预定义验证规则
  - [ ] 8.1 创建规则配置文件
    - 创建 config/validation_rules.json
    - 定义至少20个预定义规则
    - 包含格式、内容、合规性规则
    - _Requirements: 4.5_

  - [ ] 8.2 实现常见格式规则
    - 文号格式检查
    - 日期格式检查
    - 落款格式检查
    - 页眉页脚格式检查
    - _Requirements: 4.1_

  - [ ] 8.3 实现常见内容规则
    - 文书长度检查
    - 禁用词检查
    - 签名检查
    - 必填字段检查
    - _Requirements: 4.2_

  - [ ] 8.4 实现常见合规性规则
    - 案件编号检查
    - 密级标注检查
    - 收件人信息检查
    - 法规引用检查
    - _Requirements: 4.3_

- [ ] 9. 检查点 - 确保降级功能完整集成
  - 测试 AI 服务失败场景
  - 验证自动降级切换
  - 确认降级通知正确显示
  - 验证性能满足要求（<3秒）
  - 如有问题请询问用户

- [ ] 10. 实现管理和监控接口
  - [ ] 10.1 创建健康状态查询接口
    - GET /api/v1/health/status
    - 返回当前模式、健康状态、统计信息
    - _Requirements: 6.5_

  - [ ] 10.2 创建降级统计接口
    - GET /api/v1/health/fallback-stats
    - 返回降级频率、持续时间、影响请求数
    - _Requirements: 6.5_

  - [ ] 10.3 创建规则性能查询接口
    - GET /api/v1/admin/rules/performance
    - 返回每个规则的执行时间统计
    - 标识慢规则
    - _Requirements: 8.5_

  - [ ] 10.4 创建规则管理接口
    - GET /api/v1/admin/rules/list - 列出所有规则
    - PUT /api/v1/admin/rules/{rule_id}/toggle - 启用/禁用规则
    - POST /api/v1/admin/rules/reload - 重载配置
    - _Requirements: 1.4, 7.2_

  - [ ]* 10.5 为规则状态切换编写属性测试
    - **Property 3: Rule State Toggle**
    - **Validates: Requirements 1.4**

- [ ] 11. 添加系统配置
  - [x] 11.1 更新 config.py
    - 添加降级功能配置项
    - 设置默认值
    - _Requirements: 所有_

  - [ ] 11.2 更新 requirements.txt
    - 添加 watchdog（文件监控）
    - 添加其他依赖
    - _Requirements: 7.2_

  - [-] 11.3 创建启动初始化逻辑
    - 在 main.py 中初始化健康监控
    - 启动后台健康检查任务
    - 加载规则配置
    - _Requirements: 2.1_

- [ ] 12. 编写集成测试
  - [ ] 12.1 测试完整降级流程
    - 模拟 AI 服务失败
    - 验证自动切换到本地引擎
    - 验证降级通知
    - _Requirements: 3.1, 3.2, 3.4_

  - [ ] 12.2 测试恢复流程
    - 模拟 AI 服务恢复
    - 验证自动切换回正常模式
    - _Requirements: 2.5_

  - [ ] 12.3 测试并发场景
    - 多个并发请求
    - 验证降级模式下的性能
    - _Requirements: 3.5_

  - [ ] 12.4 测试配置热重载
    - 修改配置文件
    - 验证规则自动重载
    - 验证无效配置的处理
    - _Requirements: 7.2, 7.4_

- [ ] 13. 最终检查点 - 确保所有功能正常
  - 运行所有单元测试和属性测试
  - 运行所有集成测试
  - 验证性能指标
  - 检查日志记录
  - 确认文档完整
  - 如有问题请询问用户

## Notes

- 任务标记 `*` 的为可选测试任务，可以跳过以加快 MVP 开发
- 每个任务都引用了具体的需求条目以确保可追溯性
- 检查点任务确保增量验证
- 属性测试验证通用正确性属性
- 单元测试验证具体示例和边界情况
- 集成测试验证端到端流程

## Implementation Order

建议按以下顺序实现：

1. **阶段 1（基础）**: 任务 1-3 - 规则系统核心
2. **阶段 2（引擎）**: 任务 4-5 - 本地规则引擎
3. **阶段 3（监控）**: 任务 6 - 健康监控
4. **阶段 4（集成）**: 任务 7-9 - 降级功能集成
5. **阶段 5（完善）**: 任务 10-13 - 管理接口和测试

## Estimated Time

- 阶段 1: 2-3 小时
- 阶段 2: 2-3 小时
- 阶段 3: 2 小时
- 阶段 4: 2-3 小时
- 阶段 5: 2-3 小时

**总计**: 10-14 小时
