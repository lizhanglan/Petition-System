#!/bin/bash

# ONLYOFFICE服务器部署脚本
# 服务器: 101.37.24.171
# 使用方法: bash deploy-server.sh

set -e

echo "========================================="
echo "  信访智能文书生成系统 - 服务器部署"
echo "========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量
PROJECT_DIR="/opt/petition-system"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
VENV_DIR="$BACKEND_DIR/venv"

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}请使用root用户运行此脚本${NC}"
    echo "使用: sudo bash deploy-server.sh"
    exit 1
fi

echo -e "${GREEN}步骤1: 检查系统环境${NC}"
echo "-----------------------------------"

# 检查Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓${NC} Python已安装: $PYTHON_VERSION"
else
    echo -e "${RED}✗${NC} Python未安装"
    echo "安装Python: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

# 检查Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓${NC} Node.js已安装: $NODE_VERSION"
else
    echo -e "${RED}✗${NC} Node.js未安装"
    echo "安装Node.js: curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash - && sudo apt install -y nodejs"
    exit 1
fi

# 检查PostgreSQL
if command -v psql &> /dev/null; then
    echo -e "${GREEN}✓${NC} PostgreSQL已安装"
else
    echo -e "${YELLOW}⚠${NC} PostgreSQL未安装"
    echo "安装PostgreSQL: sudo apt install postgresql postgresql-contrib"
fi

# 检查Nginx
if command -v nginx &> /dev/null; then
    echo -e "${GREEN}✓${NC} Nginx已安装"
else
    echo -e "${YELLOW}⚠${NC} Nginx未安装"
    echo "安装Nginx: sudo apt install nginx"
fi

echo ""
echo -e "${GREEN}步骤2: 创建项目目录${NC}"
echo "-----------------------------------"

if [ -d "$PROJECT_DIR" ]; then
    echo -e "${YELLOW}⚠${NC} 项目目录已存在: $PROJECT_DIR"
    read -p "是否继续？这将更新现有代码 (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    mkdir -p $PROJECT_DIR
    echo -e "${GREEN}✓${NC} 创建项目目录: $PROJECT_DIR"
fi

echo ""
echo -e "${GREEN}步骤3: 克隆/更新代码${NC}"
echo "-----------------------------------"

cd /opt

if [ -d "$PROJECT_DIR/.git" ]; then
    echo "更新现有代码..."
    cd $PROJECT_DIR
    git pull origin main
    echo -e "${GREEN}✓${NC} 代码已更新"
else
    echo "请手动克隆代码到 $PROJECT_DIR"
    echo "命令: git clone YOUR_REPO_URL $PROJECT_DIR"
    exit 1
fi

echo ""
echo -e "${GREEN}步骤4: 配置后端${NC}"
echo "-----------------------------------"

cd $BACKEND_DIR

# 创建虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    echo "创建Python虚拟环境..."
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} 虚拟环境已创建"
fi

# 激活虚拟环境并安装依赖
echo "安装Python依赖..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓${NC} Python依赖已安装"

# 检查.env文件
if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo -e "${YELLOW}⚠${NC} .env文件不存在"
    if [ -f "$BACKEND_DIR/.env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓${NC} 已从.env.example创建.env文件"
        echo -e "${YELLOW}⚠${NC} 请编辑.env文件配置正确的参数"
        echo "编辑命令: vi $BACKEND_DIR/.env"
    fi
else
    echo -e "${GREEN}✓${NC} .env文件已存在"
fi

# 检查关键配置
echo "检查ONLYOFFICE配置..."
if grep -q "ONLYOFFICE_ENABLED=true" .env; then
    echo -e "${GREEN}✓${NC} ONLYOFFICE已启用"
else
    echo -e "${YELLOW}⚠${NC} ONLYOFFICE未启用"
fi

if grep -q "BACKEND_PUBLIC_URL=http://101.37.24.171:8000" .env; then
    echo -e "${GREEN}✓${NC} 后端公网URL配置正确"
else
    echo -e "${YELLOW}⚠${NC} 后端公网URL可能需要调整"
fi

echo ""
echo -e "${GREEN}步骤5: 配置systemd服务${NC}"
echo "-----------------------------------"

# 创建systemd服务文件
cat > /etc/systemd/system/petition-backend.service << EOF
[Unit]
Description=Petition System Backend
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/python run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✓${NC} systemd服务文件已创建"

# 重载systemd
systemctl daemon-reload
echo -e "${GREEN}✓${NC} systemd已重载"

# 启动服务
systemctl restart petition-backend
echo -e "${GREEN}✓${NC} 后端服务已重启"

# 设置开机自启
systemctl enable petition-backend
echo -e "${GREEN}✓${NC} 后端服务已设置开机自启"

# 检查服务状态
sleep 2
if systemctl is-active --quiet petition-backend; then
    echo -e "${GREEN}✓${NC} 后端服务运行正常"
else
    echo -e "${RED}✗${NC} 后端服务启动失败"
    echo "查看日志: sudo journalctl -u petition-backend -n 50"
    exit 1
fi

echo ""
echo -e "${GREEN}步骤6: 构建前端${NC}"
echo "-----------------------------------"

cd $FRONTEND_DIR

# 安装依赖
echo "安装Node.js依赖..."
npm install
echo -e "${GREEN}✓${NC} Node.js依赖已安装"

# 构建生产版本
echo "构建前端生产版本..."
npm run build
echo -e "${GREEN}✓${NC} 前端已构建"

echo ""
echo -e "${GREEN}步骤7: 配置Nginx${NC}"
echo "-----------------------------------"

# 创建Nginx配置
cat > /etc/nginx/sites-available/petition-system << 'EOF'
server {
    listen 80;
    server_name 101.37.24.171;

    # 前端静态文件
    location / {
        root /opt/petition-system/frontend/dist;
        try_files $uri $uri/ /index.html;
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
        
        # 增加超时时间
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }

    # 文件上传大小限制
    client_max_body_size 100M;
}
EOF

echo -e "${GREEN}✓${NC} Nginx配置文件已创建"

# 启用配置
if [ ! -L /etc/nginx/sites-enabled/petition-system ]; then
    ln -s /etc/nginx/sites-available/petition-system /etc/nginx/sites-enabled/
    echo -e "${GREEN}✓${NC} Nginx配置已启用"
fi

# 测试Nginx配置
if nginx -t 2>&1 | grep -q "successful"; then
    echo -e "${GREEN}✓${NC} Nginx配置测试通过"
else
    echo -e "${RED}✗${NC} Nginx配置测试失败"
    nginx -t
    exit 1
fi

# 重启Nginx
systemctl restart nginx
echo -e "${GREEN}✓${NC} Nginx已重启"

# 设置开机自启
systemctl enable nginx
echo -e "${GREEN}✓${NC} Nginx已设置开机自启"

echo ""
echo -e "${GREEN}步骤8: 配置防火墙${NC}"
echo "-----------------------------------"

# 检查ufw是否安装
if command -v ufw &> /dev/null; then
    # 开放端口
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 8000/tcp
    ufw allow 9090/tcp
    
    echo -e "${GREEN}✓${NC} 防火墙规则已配置"
else
    echo -e "${YELLOW}⚠${NC} ufw未安装，请手动配置防火墙"
fi

echo ""
echo "========================================="
echo -e "${GREEN}  部署完成！${NC}"
echo "========================================="
echo ""
echo "服务状态:"
echo "  后端: $(systemctl is-active petition-backend)"
echo "  Nginx: $(systemctl is-active nginx)"
echo ""
echo "访问地址:"
echo "  前端: http://101.37.24.171"
echo "  后端API: http://101.37.24.171:8000"
echo "  ONLYOFFICE: http://101.37.24.171:9090"
echo ""
echo "查看日志:"
echo "  后端: sudo journalctl -u petition-backend -f"
echo "  Nginx: sudo tail -f /var/log/nginx/error.log"
echo ""
echo "管理命令:"
echo "  重启后端: sudo systemctl restart petition-backend"
echo "  重启Nginx: sudo systemctl restart nginx"
echo "  查看状态: sudo systemctl status petition-backend"
echo ""
echo -e "${YELLOW}注意事项:${NC}"
echo "1. 请确保.env文件配置正确"
echo "2. 请确保数据库已创建并初始化"
echo "3. 请确保ONLYOFFICE服务正常运行"
echo "4. 请测试所有功能是否正常"
echo ""
echo "测试ONLYOFFICE:"
echo "  curl http://101.37.24.171:9090/healthcheck"
echo ""
echo "详细文档: ONLYOFFICE服务器部署指南.md"
echo ""
