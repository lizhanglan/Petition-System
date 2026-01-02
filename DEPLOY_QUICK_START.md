# 🚀 Docker 快速部署指南

## 一键部署（3 步完成）

### 步骤 1: 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，至少配置以下内容：
# DEEPSEEK_API_KEY=your-api-key-here
# SECRET_KEY=your-secret-key-min-32-chars
```

### 步骤 2: 启动服务
```bash
# 给部署脚本添加执行权限
chmod +x deploy.sh

# 启动所有服务
./deploy.sh start
```

### 步骤 3: 初始化数据库
```bash
# 初始化数据库和标准模板
./deploy.sh init
```

## ✅ 完成！

访问系统：
- **前端**: http://localhost
- **后端 API**: http://localhost:8000/docs
- **MinIO 控制台**: http://localhost:9001

默认管理员账号：
- 用户名: `admin`
- 密码: `admin123`

---

## 📦 包含的服务

- ✅ 前端 (Nginx + Vue3)
- ✅ 后端 (FastAPI + Python)
- ✅ 数据库 (PostgreSQL)
- ✅ 缓存 (Redis)
- ✅ 对象存储 (MinIO)

---

## 🔧 常用命令

```bash
# 查看服务状态
./deploy.sh status

# 查看日志
./deploy.sh logs

# 停止服务
./deploy.sh stop

# 重启服务
./deploy.sh restart

# 备份数据
./deploy.sh backup
```

---

## ⚠️ 注意事项

1. **必须配置 DEEPSEEK_API_KEY**，否则 AI 功能无法使用
2. **生产环境请修改所有默认密码**
3. **确保端口 80, 8000, 5432, 6379, 9000, 9001 未被占用**
4. **首次部署后请立即修改管理员密码**

---

## 📖 详细文档

查看完整部署文档：[DOCKER_DEPLOY.md](./DOCKER_DEPLOY.md)

---

**部署时间**: 约 5-10 分钟  
**系统要求**: Docker 20.10+, 4GB RAM, 20GB 磁盘
