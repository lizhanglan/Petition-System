#!/bin/bash

# 云服务器Docker部署脚本
# 使用方法: ./deploy-cloud.sh

set -e

echo "========================================="
echo "  信访智能文书生成系统 - 云服务器部署"
echo "========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker未安装${NC}"
    echo "请先安装Docker: curl -fsSL https://get.docker.com | sh"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}错误: Docker Compose未安装${NC}"
    echo "请先安装Docker Compose"
    exit 1
fi

# 检查.env文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}警告: .env文件不存在${NC}"
    echo "正在从.env.example创建.env文件..."
    cp .env.example .env
    echo -e "${YELLOW}请编辑.env文件，配置必要的环境变量：${NC}"
    echo "  - POSTGRES_PASSWORD (数据库密码)"
    echo "  - REDIS_PASSWORD (Redis密码)"
    echo "  - MINIO_ROOT_PASSWORD (MinIO密码)"
    echo "  - SECRET_KEY (JWT密钥，至少32位)"
    echo "  - DEEPSEEK_API_KEY (DeepSeek API密钥)"
    echo ""
    read -p "是否现在编辑.env文件? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} .env
    else
        echo -e "${RED}请手动编辑.env文件后重新运行此脚本${NC}"
        exit 1
    fi
fi

# 检查必要的环境变量
echo "检查环境变量配置..."
source .env

if [ -z "$DEEPSEEK_API_KEY" ] || [ "$DEEPSEEK_API_KEY" = "your-deepseek-api-key" ]; then
    echo -e "${RED}错误: 请在.env文件中配置DEEPSEEK_API_KEY${NC}"
    exit 1
fi

if [ "$SECRET_KEY" = "your-secret-key-change-in-production-min-32-chars" ]; then
    echo -e "${YELLOW}警告: 请修改SECRET_KEY为随机字符串${NC}"
    read -p "是否继续? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}✓ 环境变量检查通过${NC}"
echo ""

# 询问是否需要清理旧数据
read -p "是否清理旧的容器和数据? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "停止并删除旧容器..."
    docker-compose down -v
    echo -e "${GREEN}✓ 清理完成${NC}"
fi

# 构建镜像
echo ""
echo "开始构建Docker镜像..."
docker-compose build --no-cache

if [ $? -ne 0 ]; then
    echo -e "${RED}错误: 镜像构建失败${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 镜像构建完成${NC}"
echo ""

# 启动服务
echo "启动服务..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo -e "${RED}错误: 服务启动失败${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 服务启动成功${NC}"
echo ""

# 等待服务就绪
echo "等待服务就绪..."
sleep 10

# 检查服务状态
echo ""
echo "检查服务状态..."
docker-compose ps

# 初始化数据库
echo ""
read -p "是否初始化数据库? (首次部署选择y) (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "初始化数据库..."
    docker exec petition-backend python manual_create_tables.py
    
    echo "初始化标准模板..."
    docker exec petition-backend python init_standard_templates.py
    
    echo -e "${GREEN}✓ 数据库初始化完成${NC}"
fi

# 显示访问信息
echo ""
echo "========================================="
echo -e "${GREEN}部署完成！${NC}"
echo "========================================="
echo ""
echo "访问地址:"
echo "  前端: http://$(hostname -I | awk '{print $1}')"
echo "  后端API: http://$(hostname -I | awk '{print $1}')/api/v1"
echo "  MinIO控制台: http://$(hostname -I | awk '{print $1}'):9001"
echo ""
echo "默认账号:"
echo "  用户名: admin"
echo "  密码: admin123"
echo ""
echo "查看日志:"
echo "  docker-compose logs -f"
echo ""
echo "停止服务:"
echo "  docker-compose down"
echo ""
echo "重启服务:"
echo "  docker-compose restart"
echo ""
echo -e "${YELLOW}注意事项:${NC}"
echo "1. 请修改默认密码"
echo "2. 配置防火墙规则"
echo "3. 定期备份数据"
echo "4. 监控服务状态"
echo ""
