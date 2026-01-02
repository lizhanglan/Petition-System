# 云服务器Docker部署指南

**更新日期**: 2026-01-03  
**适用场景**: 云服务器生产环境部署

---

## 📋 部署前检查清单

### ✅ 必须修改的配置

#### 1. 前端API地址配置 ⚠️ **重要**

**问题**: 前端硬编码了 `localhost:8000`，在云服务器上无法访问

**文件**: `frontend/src/api/request.ts`

**当前配置**:
```typescript
const request = axios.create({
  baseURL: 'http://localhost:8000/api/v1',  // ❌ 错误
  timeout: 30000
})

export const longRequest = axios.create({
  baseURL: 'http://localhost:8000/api/v1',  // ❌ 错误
  timeout: 120000
})
```

**修改方案**:
```typescript
// 使用相对路径，通过nginx代理
const request = axios.create({
  baseURL: '/api/v1',  // ✅ 正确
  timeout: 30000
})

export const longRequest = axios.create({
  baseURL: '/api/v1',  // ✅ 正确
  timeout: 120000
})
```

**原理**: 
- 前端通过nginx代理访问后端
- nginx配置中 `/api/` 会转发到 `backend:8000/api/`
- 使用相对路径可以自动适配域名

---

#### 2. 环境变量配置 ⚠️ **必须**

**文件**: `.env`（从 `.env.example` 复制）

**必须修改的配置**:
```bash
# 1. 数据库密码（强密码）
POSTGRES_PASSWORD=your-strong-password-here

# 2. Redis密码（强密码）
REDIS_PASSWORD=your-strong-redis-password

# 3. MinIO密码（强密码）
MINIO_ROOT_PASSWORD=your-strong-minio-password

# 4. JWT密钥（至少32位随机字符串）
SECRET_KEY=your-very-long-random-secret-key-at-least-32-characters

# 5. DeepSeek API密钥（必填）
DEEPSEEK_API_KEY=sk-your-actual-deepseek-api-key

# 6. 华为云配置（如果使用文件预览）
HUAWEI_CLOUD_AK=your-huawei-cloud-ak
HUAWEI_CLOUD_SK=your-huawei-cloud-sk
```

**生成强密码命令**:
```bash
# Linux/Mac
openssl rand -base64 32

# 或使用Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

#### 3. MinIO公网访问配置 ⚠️ **重要**

**问题**: MinIO需要配置公网访问地址，否则文件预览无法工作

**文件**: `backend/.env`

**添加配置**:
```bash
# MinIO公网访问地址（替换为你的服务器IP或域名）
MINIO_PUBLIC_URL=http://your-server-ip:9000
# 或使用域名
MINIO_PUBLIC_URL=http://minio.yourdomain.com
```

**修改后端代码**: `backend/app/core/minio_client.py`

在 `get_file_url` 方法中使用公网地址：
```python
def get_file_url(self, object_name: str, expires: int = 3600, inline: bool = False) -> str:
    """获取文件访问URL"""
    try:
        # 使用公网地址
        public_url = os.getenv('MINIO_PUBLIC_URL', f'http://{self.endpoint}')
        url = self.client.presigned_get_object(
            self.bucket_name,
            object_name,
            expires=timedelta(seconds=expires),
            response_headers={'response-content-disposition': 'inline' if inline else 'attachment'}
        )
        # 替换内网地址为公网地址
        url = url.replace(f'http://{self.endpoint}', public_url)
        return url
    except Exception as e:
        print(f"Error generating presigned URL: {e}")
        return ""
```

---

### ✅ 推荐修改的配置

#### 4. 端口映射（可选）

**文件**: `docker-compose.yml`

**当前配置**:
```yaml
ports:
  - "80:80"      # 前端
  - "8000:8000"  # 后端
  - "5432:5432"  # PostgreSQL
  - "6379:6379"  # Redis
  - "9000:9000"  # MinIO API
  - "9001:9001"  # MinIO Console
```

**建议修改**:
```yaml
ports:
  - "80:80"      # 前端（保留）
  # 以下端口不对外暴露，仅容器内部访问
  # - "8000:8000"  # 后端（通过nginx代理）
  # - "5432:5432"  # PostgreSQL（仅内部）
  # - "6379:6379"  # Redis（仅内部）
  - "9000:9000"  # MinIO API（需要公网访问）
  - "9001:9001"  # MinIO Console（管理界面）
```

**原因**: 减少暴露的端口，提高安全性

---

#### 5. 数据持久化路径（可选）

**文件**: `docker-compose.yml`

**当前配置**:
```yaml
volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  minio_data:
    driver: local
```

**建议修改**（指定具体路径）:
```yaml
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/petition/postgres
  redis_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/petition/redis
  minio_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/petition/minio
```

**原因**: 
- 数据存储在指定目录，便于备份
- 避免Docker卷管理混乱

---

#### 6. Nginx配置优化（可选）

**文件**: `frontend/nginx.conf`

**添加HTTPS支持**（如果有SSL证书）:
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # ... 其他配置
}
```

**添加访问日志**:
```nginx
access_log /var/log/nginx/access.log;
error_log /var/log/nginx/error.log;
```

---

## 🚀 部署步骤

### 1. 准备服务器

```bash
# 安装Docker和Docker Compose
curl -fsSL https://get.docker.com | sh
sudo systemctl start docker
sudo systemctl enable docker

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. 上传代码

```bash
# 方式1: 使用git
git clone your-repository-url
cd your-project

# 方式2: 使用scp
scp -r ./project-folder user@server-ip:/path/to/project
```

### 3. 修改配置

```bash
# 复制环境变量文件
cp .env.example .env

# 编辑环境变量
nano .env

# 修改前端API地址
nano frontend/src/api/request.ts
```

### 4. 构建和启动

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 5. 初始化数据库

```bash
# 进入后端容器
docker exec -it petition-backend bash

# 运行数据库初始化
python manual_create_tables.py

# 初始化标准模板
python init_standard_templates.py

# 退出容器
exit
```

### 6. 验证部署

```bash
# 检查服务状态
docker-compose ps

# 测试前端访问
curl http://your-server-ip

# 测试后端API
curl http://your-server-ip/api/v1/health/status
```

---

## 🔒 安全建议

### 1. 防火墙配置

```bash
# 只开放必要端口
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 9000/tcp  # MinIO API
sudo ufw enable
```

### 2. 定期备份

```bash
# 备份数据库
docker exec petition-postgres pg_dump -U postgres petition_system > backup.sql

# 备份MinIO数据
docker exec petition-minio mc mirror /data /backup

# 备份到远程
rsync -avz /data/petition user@backup-server:/backups/
```

### 3. 日志监控

```bash
# 查看容器日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 设置日志轮转
# 编辑 /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

---

## 🐛 常见问题

### 问题1: 前端无法访问后端API

**症状**: 前端显示"网络错误"

**原因**: API地址配置错误

**解决**:
1. 检查 `frontend/src/api/request.ts` 是否使用相对路径
2. 检查 `frontend/nginx.conf` 代理配置是否正确
3. 重新构建前端镜像: `docker-compose build frontend`

### 问题2: MinIO文件无法访问

**症状**: 文件上传成功，但预览失败

**原因**: MinIO地址配置错误

**解决**:
1. 配置 `MINIO_PUBLIC_URL` 环境变量
2. 修改 `minio_client.py` 使用公网地址
3. 确保9000端口可以公网访问

### 问题3: 数据库连接失败

**症状**: 后端启动失败，提示数据库连接错误

**原因**: 数据库未就绪或密码错误

**解决**:
1. 检查 `.env` 中的数据库密码
2. 等待数据库健康检查通过
3. 查看数据库日志: `docker-compose logs postgres`

### 问题4: 容器启动失败

**症状**: `docker-compose up` 报错

**原因**: 端口被占用或配置错误

**解决**:
1. 检查端口占用: `netstat -tulpn | grep :80`
2. 修改端口映射
3. 检查配置文件语法

---

## 📊 性能优化

### 1. 数据库优化

```yaml
# docker-compose.yml
postgres:
  command: postgres -c shared_buffers=256MB -c max_connections=200
```

### 2. Redis优化

```yaml
redis:
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### 3. Nginx优化

```nginx
# nginx.conf
worker_processes auto;
worker_connections 1024;

# 启用缓存
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=1g;
```

---

## 📝 部署检查清单

部署前请确认：

- [ ] 修改前端API地址为相对路径
- [ ] 配置 `.env` 文件（所有密码和密钥）
- [ ] 配置MinIO公网访问地址
- [ ] 修改默认密码（数据库、Redis、MinIO）
- [ ] 配置DeepSeek API密钥
- [ ] 配置华为云密钥（如果使用）
- [ ] 检查防火墙规则
- [ ] 准备SSL证书（如果使用HTTPS）
- [ ] 配置数据备份策略
- [ ] 测试所有功能

---

## 🆘 技术支持

如遇到问题，请检查：
1. Docker日志: `docker-compose logs`
2. 容器状态: `docker-compose ps`
3. 网络连接: `docker network inspect petition-network`
4. 环境变量: `docker-compose config`

---

**更新时间**: 2026-01-03  
**文档版本**: 1.0  
**适用版本**: Docker 20.10+, Docker Compose 2.0+
