# Docker 部署指南

## 📋 前置要求

### 系统要求
- Docker 20.10+
- Docker Compose 2.0+
- 至少 4GB 可用内存
- 至少 20GB 可用磁盘空间

### 安装 Docker

#### Windows
1. 下载 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
2. 安装并启动 Docker Desktop
3. 确认安装：`docker --version` 和 `docker-compose --version`

#### Linux
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

---

## 🚀 快速开始

### 1. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量（必须配置 DEEPSEEK_API_KEY）
vi .env
```

**必须配置的变量**:
- `DEEPSEEK_API_KEY`: DeepSeek API 密钥（必填）
- `SECRET_KEY`: JWT 密钥（建议修改为随机字符串，至少 32 字符）

**可选配置**:
- `POSTGRES_PASSWORD`: 数据库密码
- `REDIS_PASSWORD`: Redis 密码
- `MINIO_ROOT_PASSWORD`: MinIO 密码

### 2. 启动服务

#### 使用部署脚本（推荐）

```bash
# 给脚本添加执行权限
chmod +x deploy.sh

# 启动所有服务
./deploy.sh start

# 初始化数据库（首次部署必须执行）
./deploy.sh init
```

#### 使用 Docker Compose

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 初始化数据库
docker-compose exec backend python manual_create_tables.py
docker-compose exec backend python init_standard_templates.py
```

### 3. 访问系统

- **前端**: http://localhost
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **MinIO 控制台**: http://localhost:9001

**默认管理员账号**（首次登录后请修改密码）:
- 用户名: admin
- 密码: admin123

---

## 📦 服务说明

### 服务列表

| 服务 | 端口 | 说明 |
|-----|------|------|
| frontend | 80 | 前端 Web 界面 |
| backend | 8000 | 后端 API 服务 |
| postgres | 5432 | PostgreSQL 数据库 |
| redis | 6379 | Redis 缓存 |
| minio | 9000, 9001 | MinIO 对象存储 |

### 数据持久化

所有数据存储在 Docker volumes 中：
- `postgres_data`: 数据库数据
- `redis_data`: Redis 数据
- `minio_data`: 文件存储数据

---

## 🔧 常用命令

### 服务管理

```bash
# 启动服务
./deploy.sh start

# 停止服务
./deploy.sh stop

# 重启服务
./deploy.sh restart

# 查看服务状态
./deploy.sh status
```

### 日志查看

```bash
# 查看所有服务日志
./deploy.sh logs

# 查看特定服务日志
./deploy.sh logs backend
./deploy.sh logs frontend

# 实时跟踪日志
docker-compose logs -f backend
```

### 数据管理

```bash
# 备份数据
./deploy.sh backup

# 初始化数据库
./deploy.sh init

# 清理所有数据（危险操作！）
./deploy.sh clean
```

### 容器操作

```bash
# 进入后端容器
docker-compose exec backend bash

# 进入数据库容器
docker-compose exec postgres psql -U postgres -d petition_system

# 重启单个服务
docker-compose restart backend

# 查看资源使用
docker stats
```

---

## 🔍 故障排查

### 1. 服务无法启动

**检查端口占用**:
```bash
# Windows
netstat -ano | findstr "80"
netstat -ano | findstr "8000"

# Linux
netstat -tlnp | grep 80
netstat -tlnp | grep 8000
```

**解决方案**: 修改 `docker-compose.yml` 中的端口映射

### 2. 数据库连接失败

**检查数据库状态**:
```bash
docker-compose logs postgres
docker-compose exec postgres pg_isready -U postgres
```

**解决方案**:
- 确认 PostgreSQL 容器正常运行
- 检查 `.env` 中的数据库配置
- 等待数据库完全启动（约 10-30 秒）

### 3. 后端 API 报错

**查看后端日志**:
```bash
docker-compose logs backend
```

**常见问题**:
- `DEEPSEEK_API_KEY` 未配置或无效
- 数据库未初始化：运行 `./deploy.sh init`
- MinIO 连接失败：检查 MinIO 服务状态

### 4. 前端无法访问后端

**检查网络连接**:
```bash
docker-compose exec frontend ping backend
curl http://localhost:8000/api/v1/health/status
```

**解决方案**:
- 确认所有服务在同一网络中
- 检查 nginx 配置中的代理设置
- 重启前端服务：`docker-compose restart frontend`

### 5. MinIO 无法访问

**检查 MinIO 状态**:
```bash
docker-compose logs minio
curl http://localhost:9000/minio/health/live
```

**解决方案**:
- 确认 MinIO 容器正常运行
- 检查 `.env` 中的 MinIO 配置
- 访问 http://localhost:9001 登录控制台

---

## 🔐 安全建议

### 生产环境部署

1. **修改默认密码**
   - 数据库密码
   - Redis 密码
   - MinIO 密码
   - JWT 密钥

2. **使用 HTTPS**
   ```yaml
   # 在 docker-compose.yml 中添加 SSL 证书
   frontend:
     volumes:
       - ./ssl:/etc/nginx/ssl
   ```

3. **限制端口暴露**
   ```yaml
   # 只暴露必要的端口
   postgres:
     ports:
       - "127.0.0.1:5432:5432"  # 只允许本地访问
   ```

4. **配置防火墙**
   ```bash
   # 只开放 80 和 443 端口
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

5. **定期备份**
   ```bash
   # 设置定时任务
   crontab -e
   # 每天凌晨 2 点备份
   0 2 * * * /path/to/deploy.sh backup
   ```

---

## 📊 性能优化

### 1. 资源限制

在 `docker-compose.yml` 中添加资源限制：

```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
      reservations:
        cpus: '1'
        memory: 1G
```

### 2. 数据库优化

```bash
# 进入数据库容器
docker-compose exec postgres psql -U postgres -d petition_system

# 执行优化脚本
\i /app/optimize_database.py
```

### 3. Redis 持久化

修改 Redis 配置以平衡性能和数据安全：

```yaml
redis:
  command: redis-server --appendonly yes --appendfsync everysec
```

---

## 🔄 更新部署

### 更新应用代码

```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建镜像
docker-compose build

# 3. 重启服务
docker-compose up -d

# 4. 查看日志确认
docker-compose logs -f
```

### 数据库迁移

```bash
# 运行数据库迁移
docker-compose exec backend alembic upgrade head
```

---

## 📝 监控和日志

### 日志管理

```bash
# 查看日志大小
docker-compose exec backend du -sh /app/logs

# 清理旧日志
docker-compose exec backend find /app/logs -name "*.log" -mtime +30 -delete
```

### 健康检查

```bash
# 检查所有服务健康状态
docker-compose ps

# 手动健康检查
curl http://localhost:8000/api/v1/health/status
curl http://localhost:8000/api/v1/health/fallback-stats
```

---

## 🆘 获取帮助

### 查看帮助信息

```bash
./deploy.sh
```

### 常见问题

1. **Q: 如何查看容器内部文件？**
   ```bash
   docker-compose exec backend ls -la /app
   ```

2. **Q: 如何导出数据库？**
   ```bash
   docker-compose exec postgres pg_dump -U postgres petition_system > backup.sql
   ```

3. **Q: 如何导入数据库？**
   ```bash
   docker-compose exec -T postgres psql -U postgres petition_system < backup.sql
   ```

4. **Q: 如何重置所有数据？**
   ```bash
   ./deploy.sh clean
   ./deploy.sh start
   ./deploy.sh init
   ```

---

## 📞 技术支持

如遇到问题，请提供以下信息：
1. 操作系统和 Docker 版本
2. 错误日志（`docker-compose logs`）
3. 服务状态（`docker-compose ps`）
4. 环境变量配置（隐藏敏感信息）

---

**部署文档版本**: 1.0  
**最后更新**: 2026-01-03  
**维护者**: Kiro AI Assistant
