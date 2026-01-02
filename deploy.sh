#!/bin/bash

# 信访智能文书生成系统 - Docker 部署脚本
# 使用方法: ./deploy.sh [start|stop|restart|logs|status]

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker 是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    print_info "Docker 和 Docker Compose 已安装"
}

# 检查环境变量文件
check_env() {
    if [ ! -f .env ]; then
        print_warn ".env 文件不存在，从 .env.example 复制"
        cp .env.example .env
        print_warn "请编辑 .env 文件，配置必要的环境变量（特别是 DEEPSEEK_API_KEY）"
        read -p "是否现在编辑 .env 文件？(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ${EDITOR:-vi} .env
        fi
    fi
}

# 启动服务
start_services() {
    print_info "启动服务..."
    docker-compose up -d
    
    print_info "等待服务启动..."
    sleep 10
    
    print_info "检查服务状态..."
    docker-compose ps
    
    print_info "服务已启动！"
    print_info "前端地址: http://localhost"
    print_info "后端地址: http://localhost:8000"
    print_info "MinIO 控制台: http://localhost:9001"
}

# 停止服务
stop_services() {
    print_info "停止服务..."
    docker-compose down
    print_info "服务已停止"
}

# 重启服务
restart_services() {
    print_info "重启服务..."
    docker-compose restart
    print_info "服务已重启"
}

# 查看日志
view_logs() {
    if [ -z "$2" ]; then
        docker-compose logs -f
    else
        docker-compose logs -f "$2"
    fi
}

# 查看状态
check_status() {
    print_info "服务状态:"
    docker-compose ps
    
    echo ""
    print_info "健康检查:"
    
    # 检查后端
    if curl -f http://localhost:8000/api/v1/health/status &> /dev/null; then
        print_info "✓ 后端服务正常"
    else
        print_error "✗ 后端服务异常"
    fi
    
    # 检查前端
    if curl -f http://localhost &> /dev/null; then
        print_info "✓ 前端服务正常"
    else
        print_error "✗ 前端服务异常"
    fi
}

# 初始化数据库
init_database() {
    print_info "初始化数据库..."
    docker-compose exec backend python manual_create_tables.py
    docker-compose exec backend python init_standard_templates.py
    print_info "数据库初始化完成"
}

# 备份数据
backup_data() {
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    print_info "备份数据到 $BACKUP_DIR..."
    
    # 备份数据库
    docker-compose exec -T postgres pg_dump -U postgres petition_system > "$BACKUP_DIR/database.sql"
    
    # 备份 MinIO 数据
    docker-compose exec -T minio mc mirror /data "$BACKUP_DIR/minio" &> /dev/null || true
    
    print_info "备份完成"
}

# 清理数据
clean_data() {
    read -p "确定要清理所有数据吗？这将删除数据库、Redis 和 MinIO 的所有数据！(yes/no) " -r
    echo
    if [[ $REPLY == "yes" ]]; then
        print_warn "清理数据..."
        docker-compose down -v
        print_info "数据已清理"
    else
        print_info "取消清理"
    fi
}

# 主函数
main() {
    check_docker
    
    case "${1:-start}" in
        start)
            check_env
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        logs)
            view_logs "$@"
            ;;
        status)
            check_status
            ;;
        init)
            init_database
            ;;
        backup)
            backup_data
            ;;
        clean)
            clean_data
            ;;
        *)
            echo "使用方法: $0 {start|stop|restart|logs|status|init|backup|clean}"
            echo ""
            echo "命令说明:"
            echo "  start   - 启动所有服务"
            echo "  stop    - 停止所有服务"
            echo "  restart - 重启所有服务"
            echo "  logs    - 查看日志 (可选: logs <service>)"
            echo "  status  - 查看服务状态"
            echo "  init    - 初始化数据库"
            echo "  backup  - 备份数据"
            echo "  clean   - 清理所有数据"
            exit 1
            ;;
    esac
}

main "$@"
