# ONLYOFFICE部署快速参考

**服务器**: 101.37.24.171  
**更新时间**: 2026-01-03 23:00  

---

## 🎯 一键部署

```bash
# 1. SSH登录服务器
ssh root@101.37.24.171

# 2. 克隆代码
cd /opt
git clone YOUR_REPO_URL petition-system
cd petition-system

# 3. 运行部署脚本
bash deploy-server.sh
```

---

## 📋 关键配置

### 后端环境变量 (`backend/.env`)

```env
# ONLYOFFICE配置（必须正确）
ONLYOFFICE_ENABLED=true
ONLYOFFICE_SERVER_URL=http://101.37.24.171:9090
BACKEND_PUBLIC_URL=http://101.37.24.171:8000
ONLYOFFICE_CALLBACK_URL=http://101.37.24.171:8000/api/v1/onlyoffice/callback

# 后端配置
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
BACKEND_RELOAD=false

# 数据库
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DB=petition_system

# MinIO
MINIO_ENDPOINT=124.70.74.202:9000

# Redis
REDIS_HOST=124.70.74.202
REDIS_PORT=6379
```

---

## 🔧 常用命令

### 服务管理

```bash
# 后端服务
sudo systemctl start petition-backend    # 启动
sudo systemctl stop petition-backend     # 停止
sudo systemctl restart petition-backend  # 重启
sudo systemctl status petition-backend   # 状态
sudo systemctl enable petition-backend   # 开机自启

# Nginx
sudo systemctl restart nginx
sudo systemctl status nginx
sudo nginx -t  # 测试配置

# 查看日志
sudo journalctl -u petition-backend -f  # 后端日志
sudo tail -f /var/log/nginx/error.log   # Nginx日志
```

### 测试命令

```bash
# 测试ONLYOFFICE
curl http://101.37.24.171:9090/healthcheck

# 测试后端
curl http://101.37.24.171:8000/api/v1/auth/me

# 测试前端
curl http://101.37.24.171

# 测试下载代理
curl http://101.37.24.171:8000/api/v1/onlyoffice/download/file/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🚀 更新部署

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
```

---

## 🐛 快速排查

### ONLYOFFICE无法加载

```bash
# 1. 检查后端日志
sudo journalctl -u petition-backend -n 50

# 2. 检查配置
cat backend/.env | grep ONLYOFFICE

# 3. 测试连接
curl http://101.37.24.171:9090/healthcheck
curl http://101.37.24.171:8000/api/v1/onlyoffice/download/file/1

# 4. 检查防火墙
sudo ufw status
```

### 后端无法启动

```bash
# 1. 查看详细日志
sudo journalctl -u petition-backend -n 100

# 2. 检查端口占用
sudo netstat -tlnp | grep 8000

# 3. 手动启动测试
cd /opt/petition-system/backend
source venv/bin/activate
python run.py
```

### 前端无法访问

```bash
# 1. 检查Nginx状态
sudo systemctl status nginx

# 2. 测试Nginx配置
sudo nginx -t

# 3. 查看Nginx日志
sudo tail -f /var/log/nginx/error.log

# 4. 检查dist目录
ls -la /opt/petition-system/frontend/dist
```

---

## 📊 端口和服务

| 服务 | 端口 | 地址 | 状态检查 |
|------|------|------|---------|
| 前端 | 80 | http://101.37.24.171 | `curl http://101.37.24.171` |
| 后端 | 8000 | http://101.37.24.171:8000 | `curl http://101.37.24.171:8000/api/v1/auth/me` |
| ONLYOFFICE | 9090 | http://101.37.24.171:9090 | `curl http://101.37.24.171:9090/healthcheck` |
| PostgreSQL | 5432 | localhost | `sudo -u postgres psql -c "SELECT 1"` |
| MinIO | 9000 | 124.70.74.202:9000 | `curl http://124.70.74.202:9000` |
| Redis | 6379 | 124.70.74.202:6379 | `redis-cli -h 124.70.74.202 ping` |

---

## 🔑 关键文件路径

```
/opt/petition-system/
├── backend/
│   ├── .env                    # 后端配置（重要！）
│   ├── venv/                   # Python虚拟环境
│   ├── run.py                  # 启动脚本
│   └── requirements.txt        # Python依赖
├── frontend/
│   ├── dist/                   # 构建输出（Nginx使用）
│   ├── package.json            # Node.js依赖
│   └── src/                    # 源代码
└── deploy-server.sh            # 部署脚本

/etc/systemd/system/
└── petition-backend.service    # 后端服务配置

/etc/nginx/
├── sites-available/
│   └── petition-system         # Nginx配置
└── sites-enabled/
    └── petition-system         # 配置软链接
```

---

## ✅ 验证清单

快速验证部署是否成功：

```bash
# 1. 服务状态
systemctl is-active petition-backend  # 应该返回 active
systemctl is-active nginx             # 应该返回 active

# 2. 端口监听
netstat -tlnp | grep 8000  # 后端
netstat -tlnp | grep 80    # Nginx

# 3. ONLYOFFICE连接
curl http://101.37.24.171:9090/healthcheck  # 应该返回 true

# 4. 后端API
curl http://101.37.24.171:8000/api/v1/auth/me  # 应该返回 401

# 5. 前端页面
curl -I http://101.37.24.171  # 应该返回 200
```

---

## 📞 紧急联系

### 服务器信息
- IP: 101.37.24.171
- SSH端口: 22
- 用户: root

### 外部服务
- MinIO: 124.70.74.202:9000
- Redis: 124.70.74.202:6379
- ONLYOFFICE: 101.37.24.171:9090

### 重要提示
1. **不要**在本地运行ONLYOFFICE功能（会一直加载）
2. **必须**在服务器上运行才能正常工作
3. **确保**BACKEND_PUBLIC_URL配置正确
4. **检查**防火墙端口是否开放

---

## 📚 相关文档

- 详细部署指南: `ONLYOFFICE服务器部署指南.md`
- 部署检查清单: `DEPLOYMENT_CHECKLIST_ONLYOFFICE.md`
- 本地开发限制: `ONLYOFFICE本地开发限制说明.md`
- 问题排查: `ONLYOFFICE问题排查.md`

---

**创建时间**: 2026-01-03 23:00  
**文档版本**: 1.0
