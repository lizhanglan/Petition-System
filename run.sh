#!/bin/bash

# ========================================
# 信访智能文书生成系统 - 统一启动脚本
# ========================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_title() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# 显示菜单
show_menu() {
    clear
    print_title "信访智能文书生成系统"
    echo ""
    echo "请选择运行模式:"
    echo ""
    echo "[1] 本地开发模式 (直接运行)"
    echo "[2] Docker 部署模式"
    echo "[3] 查看服务状态"
    echo "[4] 初始化数据库"
    echo "[5] 备份数据"
    echo "[6] 清理数据"
    echo "[0] 退出"
    echo ""
    print_title ""
    read -p "请输入选项 (0-6): " choice
    
    case $choice in
        1) local_dev ;;
        2) docker_menu ;;
        3) check_status ;;
        4) init_database ;;
        5) backup_data ;;
        6) clean_data ;;
        0) exit 0 ;;
        *) show_menu ;;
    esac
}

# ========================================
# 本地开发模式
# ========================================
local_dev() {
    clear
    print_title "本地开发模式"
    echo ""
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 未安装，请先安装 Python 3.12+"
        read -p "按回车键返回主菜单..."
        show_menu
        return
    fi
    
    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js 未安装，请先安装 Node.js 18+"
        read -p "按回车键返回主菜单..."
        show_menu
        return
    fi
    
    # 检查环境变量
    if [ ! -f .env ]; then
        print_warn ".env 文件不存在，从 .env.example 复制"
        cp .env.example .env
        print_warn "请编辑 .env 文件，配置必要的环境变量"
        read -p "是否现在编辑 .env 文件？(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ${EDITOR:-vi} .env
        fi
    fi
    
    # 检查后端依赖
    if [ ! -d backend/venv ]; then
        print_info "创建 Python 虚拟环境..."
        cd backend
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        cd ..
    fi
    
    # 检查前端依赖
    if [ ! -d frontend/node_modules ]; then
        print_info "安装前端依赖..."
        cd frontend
        npm install
        cd ..
    fi
    
    echo ""
    print_info "启动服务..."
    echo ""
    
    # 启动后端
    print_info "[1/2] 启动后端服务..."
    cd backend
    source venv/bin/activate
    python run.py &
    BACKEND_PID=$!
    cd ..
    sleep 3
    
    # 启动前端
    print_info "[2/2] 启动前端服务..."
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    
    echo ""
    print_title "系统启动完成！"
    echo ""
    print_info "后端服务: http://localhost:8000"
    print_info "前端服务: http://localhost:5173"
    print_info "API 文档: http://localhost:8000/docs"
    print_title ""
    echo ""
    print_warn "按 Ctrl+C 停止服务"
    
    # 等待用户中断
    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
    wait
}

# ========================================
# Docker 部署模式
# ========================================
docker_menu() {
    clear
    print_title "Docker 部署模式"
    echo ""
    echo "[1] 启动服务"
    echo "[2] 停止服务"
    echo "[3] 重启服务"
    echo "[4] 查看日志"
    echo "[0] 返回主菜单"
    echo ""
    read -p "请输入选项 (0-4): " docker_choice
    
    case $docker_choice in
        1) docker_start ;;
        2) docker_stop ;;
        3) docker_restart ;;
        4) docker_logs ;;
        0) show_menu ;;
        *) docker_menu ;;
    esac
}

docker_start() {
    echo ""
    print_info "检查 Docker..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        read -p "按回车键返回..."
        docker_menu
        return
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose 未安装"
        read -p "按回车键返回..."
        docker_menu
        return
    fi
    
    if [ ! -f .env ]; then
        print_warn ".env 文件不存在，从 .env.example 复制"
        cp .env.example .env
        print_warn "请编辑 .env 文件，配置必要的环境变量"
        read -p "按回车键继续..."
    fi
    
    print_info "启动 Docker 服务..."
    docker-compose up -d
    
    print_info "等待服务启动..."
    sleep 10
    
    print_info "检查服务状态..."
    docker-compose ps
    
    echo ""
    print_title "Docker 服务已启动！"
    echo ""
    print_info "前端地址: http://localhost"
    print_info "后端地址: http://localhost:8000"
    print_info "MinIO 控制台: http://localhost:9001"
    print_title ""
    read -p "按回车键返回..."
    docker_menu
}

docker_stop() {
    echo ""
    print_info "停止 Docker 服务..."
    docker-compose down
    print_info "服务已停止"
    read -p "按回车键返回..."
    docker_menu
}

docker_restart() {
    echo ""
    print_info "重启 Docker 服务..."
    docker-compose restart
    print_info "服务已重启"
    read -p "按回车键返回..."
    docker_menu
}

docker_logs() {
    echo ""
    print_info "查看日志 (按 Ctrl+C 退出)..."
    docker-compose logs -f
    docker_menu
}

# ========================================
# 查看服务状态
# ========================================
check_status() {
    clear
    print_title "服务状态"
    echo ""
    
    # 检查 Docker 服务
    echo "[Docker 服务]"
    if docker-compose ps &> /dev/null; then
        docker-compose ps
    else
        echo "Docker 服务未运行"
    fi
    
    echo ""
    echo "[本地服务]"
    
    # 检查后端
    if curl -f http://localhost:8000/api/v1/health/status &> /dev/null; then
        print_info "√ 后端服务正常 (http://localhost:8000)"
    else
        print_error "× 后端服务未运行"
    fi
    
    # 检查前端
    if curl -f http://localhost:5173 &> /dev/null; then
        print_info "√ 前端服务正常 (http://localhost:5173)"
    elif curl -f http://localhost &> /dev/null; then
        print_info "√ 前端服务正常 (http://localhost)"
    else
        print_error "× 前端服务未运行"
    fi
    
    echo ""
    print_title ""
    read -p "按回车键返回主菜单..."
    show_menu
}

# ========================================
# 初始化数据库
# ========================================
init_database() {
    clear
    print_title "初始化数据库"
    echo ""
    
    # 检查是否使用 Docker
    if docker-compose ps | grep -q "petition-backend"; then
        print_info "使用 Docker 初始化..."
        docker-compose exec backend python manual_create_tables.py
        docker-compose exec backend python init_standard_templates.py
    else
        print_info "使用本地环境初始化..."
        cd backend
        source venv/bin/activate
        python manual_create_tables.py
        python init_standard_templates.py
        cd ..
    fi
    
    echo ""
    print_info "数据库初始化完成"
    read -p "按回车键返回主菜单..."
    show_menu
}

# ========================================
# 备份数据
# ========================================
backup_data() {
    clear
    print_title "备份数据"
    echo ""
    
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    print_info "备份数据到 $BACKUP_DIR..."
    
    # 检查是否使用 Docker
    if docker-compose ps | grep -q "petition-postgres"; then
        print_info "备份 Docker 数据库..."
        docker-compose exec -T postgres pg_dump -U postgres petition_system > "$BACKUP_DIR/database.sql"
    else
        print_warn "Docker 服务未运行，跳过备份"
    fi
    
    print_info "备份完成: $BACKUP_DIR"
    read -p "按回车键返回主菜单..."
    show_menu
}

# ========================================
# 清理数据
# ========================================
clean_data() {
    clear
    print_title "清理数据"
    echo ""
    print_warn "这将删除所有数据库、Redis 和 MinIO 数据！"
    echo ""
    read -p "确定要继续吗？(yes/no): " confirm
    
    if [ "$confirm" == "yes" ]; then
        echo ""
        print_info "清理 Docker 数据..."
        docker-compose down -v
        print_info "数据已清理"
    else
        print_info "取消清理"
    fi
    
    read -p "按回车键返回主菜单..."
    show_menu
}

# ========================================
# 主函数
# ========================================
main() {
    # 如果有命令行参数，直接执行
    if [ $# -gt 0 ]; then
        case "$1" in
            dev|local) local_dev ;;
            docker) docker_start ;;
            stop) docker_stop ;;
            restart) docker_restart ;;
            logs) docker_logs ;;
            status) check_status ;;
            init) init_database ;;
            backup) backup_data ;;
            clean) clean_data ;;
            *)
                echo "使用方法: $0 [dev|docker|stop|restart|logs|status|init|backup|clean]"
                echo ""
                echo "命令说明:"
                echo "  dev     - 本地开发模式"
                echo "  docker  - Docker 部署模式"
                echo "  stop    - 停止服务"
                echo "  restart - 重启服务"
                echo "  logs    - 查看日志"
                echo "  status  - 查看状态"
                echo "  init    - 初始化数据库"
                echo "  backup  - 备份数据"
                echo "  clean   - 清理数据"
                echo ""
                echo "或直接运行 $0 进入交互式菜单"
                exit 1
                ;;
        esac
    else
        # 无参数时显示菜单
        show_menu
    fi
}

main "$@"
