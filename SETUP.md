# 信访智能文书生成系统 - 部署指南

## 系统已完成搭建

✅ 后端 FastAPI 服务（Python）  
✅ 前端 Vue 3 应用（TypeScript）  
✅ 数据库模型设计  
✅ API 接口实现  
✅ 前端页面组件  
✅ 服务连接测试  

## 服务连接测试结果

- ✓ PostgreSQL 连接成功
- ✓ MinIO 连接成功  
- ✓ DeepSeek API 连接成功
- ⚠ Redis 需要检查密码配置（可选服务，不影响核心功能）

## 快速启动

### 方式一：使用启动脚本（推荐）

双击运行 `start.bat` 文件，会自动启动前后端服务。

### 方式二：手动启动

#### 1. 启动后端

```bash
cd backend
python run.py
```

后端服务：http://localhost:8000  
API 文档：http://localhost:8000/docs

#### 2. 启动前端

```bash
cd frontend
npm run dev
```

前端服务：http://localhost:5173

## 首次使用

1. 访问 http://localhost:5173
2. 点击"注册"创建账号
3. 登录后即可使用系统

## 核心功能

### 1. 文件管理
- 上传 PDF、Word 文件
- 在线预览
- 文件列表管理

### 2. 文件研判
- AI 智能研判文书内容
- 错误标注与建议
- 在线修正

### 3. 文书生成
- AI 对话式生成
- 模板选择
- 实时预览

### 4. 模板管理
- 创建自定义模板
- 模板列表查询
- 快速使用模板

### 5. 文书管理
- 查看生成的文书
- 编辑文书内容
- 版本管理

## 技术架构

```
前端: Vue 3 + TypeScript + Element Plus + ProseMirror
后端: Python + FastAPI + PostgreSQL + Redis + MinIO
AI: DeepSeek API
预览: 华为云 Office 预览服务
```

## 项目结构

```
├── backend/              # 后端代码
│   ├── app/
│   │   ├── api/         # API 路由
│   │   ├── core/        # 核心配置
│   │   ├── models/      # 数据模型
│   │   └── services/    # 业务服务
│   └── run.py          # 启动文件
├── frontend/            # 前端代码
│   ├── src/
│   │   ├── api/        # API 接口
│   │   ├── stores/     # 状态管理
│   │   ├── views/      # 页面组件
│   │   └── router/     # 路由配置
│   └── package.json
├── .env                # 环境配置
└── start.bat          # 启动脚本
```

## 注意事项

1. **数据库初始化**：首次启动时会自动创建数据库表
2. **Redis 配置**：如果 Redis 连接失败，系统仍可正常运行，但缓存功能不可用
3. **文件上传**：确保 MinIO 服务正常运行
4. **API 密钥**：DeepSeek API 密钥已配置，请勿泄露

## 常见问题

### Q: 后端启动失败？
A: 检查 PostgreSQL 是否运行，端口 5432 是否被占用

### Q: 前端无法连接后端？
A: 确认后端服务已启动在 http://localhost:8000

### Q: 文件上传失败？
A: 检查 MinIO 服务是否正常，配置是否正确

### Q: AI 功能不可用？
A: 检查 DeepSeek API 密钥是否有效，网络是否正常

## 开发文档

- [后端开发说明](backend/README.md)
- [前端开发说明](frontend/README.md)
- [需求规格说明书](信访智能文书生成系统需求规格说明书（最终版）.md)

## 下一步开发建议

1. **完善文档解析**：实现 PDF/Word 文件内容提取
2. **增强 AI 研判**：优化提示词，提高研判准确性
3. **富文本编辑器**：集成 ProseMirror 实现高级编辑功能
4. **版本对比**：实现结构化 diff 算法
5. **模板提取**：完善模板智能识别功能
6. **批量操作**：支持批量文件上传和处理
7. **导出功能**：实现文书导出为 PDF/Word
8. **权限管理**：如需多角色，可扩展权限系统

## 技术支持

如有问题，请查看：
- API 文档：http://localhost:8000/docs
- 项目 README：README.md
