# ONLYOFFICE文档索引

**更新日期**: 2026-01-04

---

## 核心文档（必读）

### 1. [ONLYOFFICE集成完整指南](./ONLYOFFICE集成完整指南.md)

**适用人群**: 开发人员、运维人员、项目经理

**内容概要**:
- 项目背景和重构目标
- 完整的技术架构图
- 详细的实施步骤（4个阶段）
- 核心代码实现和说明
- 部署配置指南
- 13个问题的完整解决历程
- 测试验证清单
- 日常维护指南

**何时阅读**:
- 首次部署ONLYOFFICE时
- 需要了解整体架构时
- 进行系统维护时
- 培训新团队成员时

---

### 2. [ONLYOFFICE问题排查手册](./ONLYOFFICE问题排查手册.md)

**适用人群**: 运维人员、技术支持、开发人员

**内容概要**:
- 快速诊断脚本和健康检查清单
- 10个常见问题的详细排查步骤
- 错误代码对照表
- 日志分析技巧
- 紧急恢复方案
- 预防措施和监控告警

**何时阅读**:
- 遇到问题需要快速解决时
- 进行故障排查时
- 设置监控告警时
- 制定应急预案时

---

## 问题修复文档（按时间顺序）

### 2026-01-03

1. [ONLYOFFICE真正的问题-拦截器双重提取](./troubleshooting/ONLYOFFICE真正的问题-拦截器双重提取.md)
   - Axios拦截器导致的data双重提取问题

2. [ONLYOFFICE编辑器缓存问题最终解决方案](./troubleshooting/ONLYOFFICE编辑器缓存问题最终解决方案.md)
   - Nginx强缓存问题
   - 浏览器缓存清除方案

3. [ONLYOFFICE-HEAD请求修复完成](./troubleshooting/ONLYOFFICE-HEAD请求修复完成.md)
   - 后端支持HEAD方法
   - ONLYOFFICE服务器兼容性

4. [ONLYOFFICE编辑器加载问题修复](./troubleshooting/ONLYOFFICE编辑器加载问题修复.md)
   - Vue v-else导致DOM不存在
   - 改用v-show解决

### 2026-01-04

5. [ONLYOFFICE-JWT验证错误修复](./troubleshooting/ONLYOFFICE-JWT验证错误修复.md)
   - 禁用JWT验证
   - errorCode: -20 解决方案

6. [ONLYOFFICE-私有IP访问问题修复](./troubleshooting/ONLYOFFICE-私有IP访问问题修复.md)
   - 配置allowPrivateIPAddress
   - docservice进程重启

7. [ONLYOFFICE-缓存文件403错误修复](./troubleshooting/ONLYOFFICE-缓存文件403错误修复.md)
   - 禁用secure_link验证
   - Nginx配置修改

8. [ONLYOFFICE-预览布局优化](./troubleshooting/ONLYOFFICE-预览布局优化.md)
   - Files.vue布局优化
   - Review.vue布局优化
   - CSS flex布局应用

---

## 开发文档

### 实现文档

1. [ONLYOFFICE集成实现完成](./development/ONLYOFFICE集成实现完成.md)
   - 后端实现细节
   - API端点说明

2. [ONLYOFFICE前端集成完成](./development/ONLYOFFICE前端集成完成.md)
   - OnlyOfficeEditor组件
   - 各页面集成方案

3. [ONLYOFFICE重构总结](./development/ONLYOFFICE重构总结.md)
   - 重构决策和理由
   - 技术选型

### 规划文档

1. [ONLYOFFICE重构方案](./development/ONLYOFFICE重构方案.md)
   - 初始重构计划
   - 技术方案设计

2. [ONLYOFFICE重构任务清单](./development/ONLYOFFICE重构任务清单.md)
   - 任务分解
   - 进度跟踪

3. [ONLYOFFICE快速开始指南](./development/ONLYOFFICE快速开始指南.md)
   - 快速上手指南
   - 基本使用方法

---

## 部署文档

1. [ONLYOFFICE部署配置指南](./deployment/ONLYOFFICE部署配置指南.md)
   - Docker部署步骤
   - 环境变量配置

2. [ONLYOFFICE服务器部署指南](../ONLYOFFICE服务器部署指南.md)
   - 服务器环境准备
   - 独立部署方案

---

## 测试文档

1. [ONLYOFFICE测试状态-最新](../ONLYOFFICE测试状态-最新.md)
   - 当前测试状态
   - 已完成的修复列表
   - 下一步测试计划

2. [ONLYOFFICE测试指南](../ONLYOFFICE测试指南.md)
   - 功能测试清单
   - 测试步骤说明

3. [ONLYOFFICE验证测试方案](./development/ONLYOFFICE验证测试方案.md)
   - 验证测试计划
   - 测试用例

---

## 快速参考

### 快速修复

- [快速修复部署](../快速修复部署.md) - 紧急修复步骤
- [ONLYOFFICE修复检查清单](../ONLYOFFICE修复检查清单.md) - 修复验证清单
- [ONLYOFFICE快速参考卡](../ONLYOFFICE快速参考卡.md) - 常用命令速查

### 浏览器问题

- [浏览器缓存清除指南](./troubleshooting/浏览器缓存清除指南.md)
- [快速解决-浏览器缓存问题](../快速解决-浏览器缓存问题.md)

---

## 归档文档

以下文档已被新文档替代，保留作为历史记录：

1. [ONLYOFFICE集成完成总结](../ONLYOFFICE集成完成总结.md)
2. [ONLYOFFICE集成完成总结-最终版](../ONLYOFFICE集成完成总结-最终版.md)
3. [ONLYOFFICE集成准备就绪](../ONLYOFFICE集成准备就绪.md)
4. [ONLYOFFICE问题排查](../ONLYOFFICE问题排查.md)
5. [ONLYOFFICE问题最终解决方案](../ONLYOFFICE问题最终解决方案.md)
6. [ONLYOFFICE数据流排查方案](../ONLYOFFICE数据流排查方案.md)

---

## 文档使用建议

### 新手入门路径

1. 阅读 [ONLYOFFICE集成完整指南](./ONLYOFFICE集成完整指南.md) 了解整体架构
2. 按照指南进行部署
3. 遇到问题时查阅 [ONLYOFFICE问题排查手册](./ONLYOFFICE问题排查手册.md)
4. 参考具体的问题修复文档

### 运维人员路径

1. 熟悉 [ONLYOFFICE问题排查手册](./ONLYOFFICE问题排查手册.md)
2. 设置监控和告警
3. 定期执行健康检查
4. 遇到新问题时记录并更新文档

### 开发人员路径

1. 阅读 [ONLYOFFICE集成完整指南](./ONLYOFFICE集成完整指南.md) 的核心代码部分
2. 查看具体的实现文档
3. 参考前端和后端集成文档
4. 进行功能开发和测试

---

## 文档维护

### 更新原则

- 每次重大修复后更新相关文档
- 每月审查文档准确性
- 及时归档过时文档
- 保持文档结构清晰

### 贡献指南

如需更新文档，请：
1. 确保内容准确完整
2. 使用清晰的标题和结构
3. 提供具体的命令和代码示例
4. 更新本索引文件

---

## 联系方式

- 技术支持：Kiro AI Assistant
- 项目仓库：https://github.com/lizhanglan/Petition-System
- 文档位置：`docs/` 目录

---

**最后更新**: 2026-01-04  
**文档版本**: 1.0
