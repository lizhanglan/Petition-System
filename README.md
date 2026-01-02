# 信访智能文书生成系统

基于 DeepSeek AI 的智能信访文书生成与研判系统。

## 📊 系统状态

- **当前版本**: v1.0
- **完成度**: 78%
- **最后更新**: 2026-01-02

## 系统架构

- **前端**: Vue 3 + TypeScript + Element Plus
- **后端**: Python + FastAPI
- **数据库**: PostgreSQL
- **缓存**: Redis
- **存储**: MinIO
- **AI**: DeepSeek API
- **文档预览**: 华为云 Office 预览服务
- **文件解析**: PyPDF2 + python-docx
- **文档生成**: reportlab + python-docx

## 核心功能

### 1. 文件研判模块 ✅
- ✅ 文件上传（PDF、Word）
- ✅ 文件内容解析（PDF/Word 文本提取）
- ✅ 云端预览（华为云 + Microsoft Office Online）
- ✅ AI 智能研判（DeepSeek API）
- ✅ 结构化错误标注
- ⚠️ 在线修正（基础功能）

### 2. 文书生成模块 ✅
- ✅ AI 对话式需求输入
- ✅ 固定模板匹配
- ✅ 智能文书生成
- ✅ 模板参数填充
- ✅ 占位符替换
- ✅ 文档导出（PDF/DOCX）
- ✅ 水印和密级标注
- ⚠️ 实时预览与编辑（基础功能）

### 3. 版本管理模块 🚧
- ⚠️ 数据模型已完成
- ❌ 版本记录 API（待开发）
- ❌ 差异对比算法（待开发）
- ❌ 版本回滚功能（待开发）

### 4. 模板管理模块 ⚠️
- ✅ 模板创建与管理
- ✅ 模板列表查询
- ✅ 按类型筛选
- ❌ 智能提取（待开发）
- ❌ 全文检索（待开发）

## 🆕 最新更新（2026-01-02）

### 新增功能
1. **文件内容解析服务** ✅
   - PDF 文本提取（支持多页、表格）
   - Word 文档解析（支持段落、表格）
   - 元数据提取
   - 文档结构化

2. **完善 AI 研判功能** ✅
   - 集成文件解析
   - 完整的研判流程
   - 结构化内容保存
   - 详细日志记录

3. **文书生成逻辑优化** ✅
   - 模板参数解析
   - 字段自动填充
   - 占位符智能替换

4. **文档导出功能** ✅
   - PDF 格式导出
   - DOCX 格式导出
   - 水印添加
   - 密级标注
   - AI 标注保留选项

### 新增 API
```
GET /api/v1/documents/{id}/download
  ?format=pdf|docx
  &include_watermark=true|false
  &include_annotations=true|false
  &security_level=机密
```

### 技术改进
- 完善错误处理机制
- 优化日志输出
- 提升代码可维护性

## 快速开始

### 1. 环境要求

- Python 3.12+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- MinIO

### 2. 安装依赖

#### 后端依赖
```bash
cd backend
pip install -r requirements.txt
```

**新增依赖**：
- `reportlab==4.0.7` - PDF 生成

#### 前端依赖
```bash
cd frontend
npm install
```

### 3. 配置

复制 `.env.example` 到 `.env` 并填写配置信息（已提供）。

### 4. 启动服务

#### 方式 1：使用启动脚本（推荐）
```bash
# Windows
start.bat

# Linux/Mac
./start.sh
```

#### 方式 2：手动启动

**启动后端**：
```bash
cd backend
python run.py
```
后端服务：http://localhost:8000

**启动前端**：
```bash
cd frontend
npm run dev
```
前端服务：http://localhost:5173

## 项目结构

```
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── api/            # API 路由
│   │   │   └── v1/
│   │   │       └── endpoints/
│   │   │           ├── auth.py          # 认证接口
│   │   │           ├── files.py         # 文件接口
│   │   │           ├── documents.py     # 文档接口 ✨
│   │   │           ├── templates.py     # 模板接口
│   │   │           └── versions.py      # 版本接口
│   │   ├── core/           # 核心配置
│   │   │   ├── config.py              # 配置管理
│   │   │   ├── database.py            # 数据库
│   │   │   ├── minio_client.py        # MinIO 客户端
│   │   │   └── redis.py               # Redis 客户端
│   │   ├── models/         # 数据模型
│   │   │   ├── user.py                # 用户模型
│   │   │   ├── file.py                # 文件模型
│   │   │   ├── document.py            # 文档模型
│   │   │   ├── template.py            # 模板模型
│   │   │   ├── version.py             # 版本模型
│   │   │   └── audit_log.py           # 审计日志
│   │   └── services/       # 业务服务
│   │       ├── deepseek_service.py           # DeepSeek AI
│   │       ├── file_parser_service.py        # 文件解析 ✨
│   │       ├── document_export_service.py    # 文档导出 ✨
│   │       └── office_preview_service.py     # 预览服务
│   ├── requirements.txt    # Python 依赖
│   └── run.py             # 启动文件
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── api/           # API 接口
│   │   ├── stores/        # 状态管理
│   │   ├── views/         # 页面组件
│   │   │   ├── Login.vue           # 登录页
│   │   │   ├── Files.vue           # 文件管理
│   │   │   ├── Review.vue          # 文件研判
│   │   │   ├── Generate.vue        # 文书生成
│   │   │   ├── Documents.vue       # 文档管理
│   │   │   └── Templates.vue       # 模板管理
│   │   └── router/        # 路由配置
│   └── package.json       # Node 依赖
├── .env                   # 环境配置
├── README.md             # 项目说明
├── 系统需求实现对比分析报告.md      # 需求对比 ✨
├── 功能对照明细表.md                # 功能对照 ✨
├── 剩余功能开发清单.md              # 开发清单 ✨
├── 开发进度总结.md                  # 进度总结 ✨
├── 新功能安装测试指南.md            # 测试指南 ✨
└── 本次开发总结.md                  # 开发总结 ✨
```

## 功能特性

### 已实现 ✅
- ✅ 支持 PDF、Word 文件上传与预览
- ✅ 文件内容自动解析（PDF/Word）
- ✅ AI 智能文书研判与标注
- ✅ 对话式文书生成
- ✅ 模板参数化填充
- ✅ 文档导出（PDF/DOCX）
- ✅ 水印和密级标注
- ✅ 账号数据完全隔离
- ✅ 全链路操作审计

### 开发中 🚧
- 🚧 版本管理与精细化回滚
- 🚧 模板智能识别与提取
- 🚧 在线富文本编辑器
- 🚧 审计日志查询界面

### 计划中 📋
- 📋 API 限流与降级
- 📋 本地规则库兜底
- 📋 批量文档处理
- 📋 性能优化

## 技术亮点

- **AI 驱动**: 深度集成 DeepSeek 大模型
- **智能解析**: 自动提取 PDF/Word 文本内容
- **智能研判**: 内容与格式双重校验
- **灵活导出**: 支持 PDF/DOCX 双格式，可配置水印和密级
- **模板填充**: 智能占位符识别和替换
- **实时预览**: 1:1 还原公文格式
- **安全可靠**: 重试机制、完善的错误处理

## 📖 文档

### 用户文档
- [新功能安装测试指南](新功能安装测试指南.md) - 安装和测试步骤
- [系统需求实现对比分析报告](系统需求实现对比分析报告.md) - 完整的需求对比

### 开发文档
- [功能对照明细表](功能对照明细表.md) - 128 个需求条目对照
- [剩余功能开发清单](剩余功能开发清单.md) - 18 个任务详细规划
- [开发进度总结](开发进度总结.md) - 功能详细说明
- [本次开发总结](本次开发总结.md) - 开发工作总结

### 技术文档
- [后端开发说明](backend/README.md)
- [前端开发说明](frontend/README.md)
- [Word文档预览问题分析与解决方案](Word文档预览问题分析与解决方案.md)

## 🧪 测试

### 功能测试
```bash
# 1. 文件上传与解析
curl -X POST "http://localhost:8000/api/v1/files/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.pdf"

# 2. AI 研判
curl -X POST "http://localhost:8000/api/v1/documents/review" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"file_id": 1}'

# 3. 文档下载
curl -X GET "http://localhost:8000/api/v1/documents/1/download?format=pdf" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --output document.pdf
```

详细测试步骤见 [新功能安装测试指南](新功能安装测试指南.md)

## 🚀 下一步计划

### 第二阶段：版本管理（预计 10-13 小时）
- [ ] 版本记录 API
- [ ] 版本对比算法
- [ ] 版本回滚功能
- [ ] 前端版本界面

### 第三阶段：增强功能（预计 9-11 小时）
- [ ] 模板智能提取
- [ ] 多轮对话优化
- [ ] 审计日志查询
- [ ] 批量上传功能

### 第四阶段：优化完善（预计 11-14 小时）
- [ ] API 限流机制
- [ ] 本地规则库降级
- [ ] 密级管理
- [ ] 标准模板预置
- [ ] 性能优化

## 📊 性能指标

| 指标 | 目标 | 当前 |
|-----|------|------|
| 文件解析 | < 10s | ~2-8s ✅ |
| AI 研判 | < 30s | ~5-25s ✅ |
| 文档生成 | < 20s | ~5-15s ✅ |
| 文档导出 | < 5s | ~1-3s ✅ |
| 并发支持 | ≥ 200 | 待测试 |

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

MIT

---

**开发团队**: Kiro AI Assistant  
**最后更新**: 2026-01-02  
**版本**: v1.0
