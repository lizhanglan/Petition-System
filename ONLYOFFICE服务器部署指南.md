# ONLYOFFICE服务器部署指南

**服务器**: 101.37.24.171  
**部署时间**: 2026-01-03  

---

## 📋 部署前检查清单

### 1. 服务器环境
- [ ] 服务器IP: 101.37.24.171
- [ ] 操作系统: Linux (推荐 Ubuntu 20.04+)
- [ ] Python 3.9+
- [ ] Node.js 16+
- [ ] PostgreSQL 13+
- [ ] Redis
- [ ] Nginx

### 2. 端口开放
- [ ] 8000 - 后端API
- [ ] 80 - Nginx HTTP
- [ ] 443 - Nginx HTTPS (可选)
- [ ] 9090 - ONLYOFFICE (已开放)
- [ ] 5432 - PostgreSQL (内网)
- [ ] 6379 - Redis (内网)

### 3. 外部服务
- [ ] MinIO: 124.70.74.202:9000 (可访问)
- [ ] Redis: 124.70.74.202:6379 (可访问)
- [ ] ONLYOFFICE: 101.37.24.171:9090 (已部署)

---

## 🚀 部署步骤

### 步骤1: 克隆代码到服务器

```bash
# SSH登录服务器
ssh root@101.37.24.171

# 克隆代码
cd /opt
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git petition-system
cd petition-system
```

---

### 步骤2: 配置后端环境

#### 2.1 安装Python依赖

```bash
cd /opt/petition-system/backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 2.2 配置环境变量

```bash
# 编辑 .env 文件
vi .env
```

**关键配置**（确保这些配置正确）:

```env
# PostgreSQL（使用服务器本地数据库）
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DB=petition_system
POSTGRES_USER=postgres
POSTGRES_PASSWORD=YOUR_PASSWORD

# Redis（使用远程Redis）
REDIS_HOST=124.70.74.202
REDIS_PORT=6379
REDIS_PASSWORD=lzl123456
REDIS_DB=0

# MinIO（使用远程MinIO）
MINIO_ENDPOINT=124.70.74.202:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=petition-files
MINIO_SECURE=false

# 后端服务配置
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
BACKEND_RELOAD=false  # 生产环境关闭自动重载

# ONLYOFFICE配置（关键！）
ONLYOFFICE_ENABLED=true
ONLYOFFICE_SERVER_URL=http://101.37.24.171:9090
ONLYOFFICE_JWT_ENABLED=false
ONLYOFFICE_CALLBACK_URL=http://101.37.24.171:8000/api/v1/onlyoffice/callback
BACKEND_PUBLIC_URL=http://101.37.24.171:8000

# DeepSeek API
DEEPSEEK_API_KEY=sk-c6b281bc3770435e90db4daf82363bd4
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# 华为云预览服务（降级备用）
OFFICE_HTTP=https://officeweb365.apistore.huaweicloud.com/v2/gateway/fileurl
OFFICE_API_KEY=073199c52ea7457bafdfd84d1c0db36d
OFFICE_APP_SECRET=03d249b5c1ca4f6bbbc6944e7f9330ab
OFFICE_MCP_APP_CODE=C747B73AFB51F4E17A87D031D2205DC4
OFFICE_X_APIG_APP_CODE=59e6a266eeb44402ac63bb1730cd02f69bc1f77b17e4497fb7d432225656a744
```

#### 2.3 初始化数据库

```bash
# 创建数据库
sudo -u postgres psql
CREATE DATABASE petition_system;
\q

# 运行数据库初始化脚本
python create_db.py

# 初始化标准模板
python init_standard_templates.py
```

#### 2.4 使用systemd管理后端服务

创建服务文件：

```bash
sudo vi /etc/systemd/system/petition-backend.service
```

内容：

```ini
[Unit]
Description=Petition System Backend
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/petition-system/backend
Environment="PATH=/opt/petition-system/backend/venv/bin"
ExecStart=/opt/petition-system/backend/venv/bin/python run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
# 重载systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start petition-backend

# 设置开机自启
sudo systemctl enable petition-backend

# 查看状态
sudo systemctl status petition-backend

# 查看日志
sudo journalctl -u petition-backend -f
```

---

### 步骤3: 配置前端

#### 3.1 安装Node.js依赖

```bash
cd /opt/petition-system/frontend

# 安装依赖
npm install

# 构建生产版本
npm run build
```

#### 3.2 配置Nginx

创建Nginx配置：

```bash
sudo vi /etc/nginx/sites-available/petition-system
```

内容：

```nginx
server {
    listen 80;
    server_name 101.37.24.171;

    # 前端静态文件
    location / {
        root /opt/petition-system/frontend/dist;
        try_files $uri $uri/ /index.html;
        
        # 添加CORS头（如果需要）
        add_header Access-Control-Allow-Origin *;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # 增加超时时间（用于AI处理）
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }

    # 文件上传大小限制
    client_max_body_size 100M;
}
```

启用配置：

```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/petition-system /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx

# 设置开机自启
sudo systemctl enable nginx
```

---

### 步骤4: 配置防火墙

```bash
# 开放必要端口
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 9090/tcp

# 启用防火墙
sudo ufw enable

# 查看状态
sudo ufw status
```

---

### 步骤5: 验证ONLYOFFICE连接

#### 5.1 测试ONLYOFFICE服务

```bash
# 测试ONLYOFFICE健康检查
curl http://101.37.24.171:9090/healthcheck

# 测试API脚本
curl http://101.37.24.171:9090/web-apps/apps/api/documents/api.js
```

#### 5.2 测试后端代理端点

```bash
# 获取认证token（先登录系统）
TOKEN="YOUR_JWT_TOKEN"

# 测试配置API
curl -X POST http://101.37.24.171:8000/api/v1/onlyoffice/config \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"file_id": 1, "mode": "view"}'

# 测试下载代理
curl http://101.37.24.171:8000/api/v1/onlyoffice/download/file/1 \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔧 部署后配置

### 1. 确保ONLYOFFICE可以访问后端

ONLYOFFICE需要能够访问：
- `http://101.37.24.171:8000/api/v1/onlyoffice/download/file/{id}`
- `http://101.37.24.171:8000/api/v1/onlyoffice/download/document/{id}`
- `http://101.37.24.171:8000/api/v1/onlyoffice/callback`

**测试方法**（在ONLYOFFICE服务器上）:

```bash
# SSH到ONLYOFFICE服务器
ssh root@101.37.24.171

# 测试后端连接
curl http://101.37.24.171:8000/api/v1/auth/me

# 应该返回401（未认证），说明后端可访问
```

### 2. 配置CORS（如果需要）

如果遇到跨域问题，在后端添加CORS配置：

```python
# backend/app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://101.37.24.171", "http://101.37.24.171:9090"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📊 部署验证清单

### 后端验证
- [ ] 后端服务运行: `systemctl status petition-backend`
- [ ] API可访问: `curl http://101.37.24.171:8000/api/v1/auth/me`
- [ ] 数据库连接正常
- [ ] Redis连接正常
- [ ] MinIO连接正常

### 前端验证
- [ ] Nginx运行: `systemctl status nginx`
- [ ] 前端页面可访问: `http://101.37.24.171`
- [ ] 可以登录系统
- [ ] API代理正常工作

### ONLYOFFICE验证
- [ ] ONLYOFFICE服务运行: `curl http://101.37.24.171:9090/healthcheck`
- [ ] 配置API正常: 测试 `/api/v1/onlyoffice/config`
- [ ] 下载代理正常: 测试 `/api/v1/onlyoffice/download/file/{id}`
- [ ] 回调端点可访问: 测试 `/api/v1/onlyoffice/callback`

### 功能验证
- [ ] 文件上传
- [ ] 文件预览（ONLYOFFICE）
- [ ] 文件编辑（ONLYOFFICE）
- [ ] 文书生成
- [ ] 文书预览（ONLYOFFICE）
- [ ] 文书在线编辑（ONLYOFFICE）
- [ ] 文件研判

---

## 🐛 常见问题排查

### 问题1: 后端无法启动

**检查**:
```bash
# 查看日志
sudo journalctl -u petition-backend -n 50

# 检查端口占用
sudo netstat -tlnp | grep 8000

# 检查Python环境
source /opt/petition-system/backend/venv/bin/activate
python --version
```

### 问题2: ONLYOFFICE无法加载文档

**检查**:
```bash
# 1. 检查后端日志
sudo journalctl -u petition-backend -f

# 2. 测试ONLYOFFICE到后端的连接
curl http://101.37.24.171:8000/api/v1/onlyoffice/download/file/1

# 3. 检查防火墙
sudo ufw status

# 4. 检查Nginx日志
sudo tail -f /var/log/nginx/error.log
```

### 问题3: 前端无法访问

**检查**:
```bash
# 检查Nginx状态
sudo systemctl status nginx

# 检查Nginx配置
sudo nginx -t

# 查看Nginx日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

## 🔄 更新部署

当代码更新后：

```bash
# 1. 拉取最新代码
cd /opt/petition-system
git pull origin main

# 2. 更新后端
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart petition-backend

# 3. 更新前端
cd ../frontend
npm install
npm run build
sudo systemctl reload nginx

# 4. 验证
sudo systemctl status petition-backend
sudo systemctl status nginx
```

---

## 📝 环境变量对比

### 本地开发环境
```env
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
BACKEND_RELOAD=true
ONLYOFFICE_ENABLED=false  # 本地禁用
BACKEND_PUBLIC_URL=http://localhost:8000
```

### 服务器生产环境
```env
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
BACKEND_RELOAD=false  # 生产环境关闭
ONLYOFFICE_ENABLED=true  # 服务器启用
BACKEND_PUBLIC_URL=http://101.37.24.171:8000
ONLYOFFICE_CALLBACK_URL=http://101.37.24.171:8000/api/v1/onlyoffice/callback
```

---

## 🎯 部署完成后测试

### 1. 基础功能测试
1. 访问 `http://101.37.24.171`
2. 登录系统
3. 上传文件
4. 查看文件列表

### 2. ONLYOFFICE功能测试
1. 点击文件"预览"按钮
2. 应该看到ONLYOFFICE编辑器加载
3. 文档内容正常显示
4. 可以滚动查看

### 3. 文书生成测试
1. 进入文书生成页面
2. 选择模板并生成文书
3. 右侧应该显示ONLYOFFICE预览
4. 文书内容正常显示

### 4. 在线编辑测试
1. 进入文书管理页面
2. 点击"在线编辑"按钮
3. ONLYOFFICE编辑器打开
4. 可以编辑文档
5. 保存成功

---

## 📞 技术支持

如果遇到问题：

1. **查看日志**:
   - 后端: `sudo journalctl -u petition-backend -f`
   - Nginx: `sudo tail -f /var/log/nginx/error.log`
   - 浏览器控制台: F12

2. **检查配置**:
   - 后端: `/opt/petition-system/backend/.env`
   - Nginx: `/etc/nginx/sites-available/petition-system`

3. **测试连接**:
   - ONLYOFFICE: `curl http://101.37.24.171:9090/healthcheck`
   - 后端: `curl http://101.37.24.171:8000/api/v1/auth/me`
   - 前端: `curl http://101.37.24.171`

---

**创建时间**: 2026-01-03 23:00  
**文档版本**: 1.0  
**服务器**: 101.37.24.171
