@echo off
chcp 65001 >nul
REM ========================================
REM 信访智能文书生成系统 - 统一启动脚本
REM ========================================

setlocal enabledelayedexpansion

REM 显示菜单
:menu
cls
echo ========================================
echo 信访智能文书生成系统
echo ========================================
echo.
echo 请选择运行模式:
echo.
echo [1] 本地开发模式 (直接运行)
echo [2] Docker 部署模式
echo [3] 查看服务状态
echo [4] 初始化数据库
echo [5] 备份数据
echo [6] 清理数据
echo [0] 退出
echo.
echo ========================================
set /p choice="请输入选项 (0-6): "

if "%choice%"=="1" goto local_dev
if "%choice%"=="2" goto docker_menu
if "%choice%"=="3" goto status
if "%choice%"=="4" goto init_db
if "%choice%"=="5" goto backup
if "%choice%"=="6" goto clean
if "%choice%"=="0" goto end
goto menu

REM ========================================
REM 本地开发模式
REM ========================================
:local_dev
cls
echo ========================================
echo 本地开发模式
echo ========================================
echo.

REM 检查 Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python 未安装，请先安装 Python 3.12+
    pause
    goto menu
)

REM 检查 Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js 未安装，请先安装 Node.js 18+
    pause
    goto menu
)

REM 检查环境变量
if not exist .env (
    echo [WARN] .env 文件不存在，从 .env.example 复制
    copy .env.example .env
    echo [WARN] 请编辑 .env 文件，配置必要的环境变量
    pause
)

REM 检查后端依赖
if not exist backend\venv (
    echo [INFO] 创建 Python 虚拟环境...
    cd backend
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
    cd ..
)

REM 检查前端依赖
if not exist frontend\node_modules (
    echo [INFO] 安装前端依赖...
    cd frontend
    call npm install
    cd ..
)

echo.
echo [INFO] 启动服务...
echo.

REM 启动后端
echo [1/2] 启动后端服务...
start "Backend Server" cmd /k "cd backend && venv\Scripts\activate && python run.py"
timeout /t 3 /nobreak >nul

REM 启动前端
echo [2/2] 启动前端服务...
start "Frontend Server" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo 系统启动完成！
echo ========================================
echo 后端服务: http://localhost:8000
echo 前端服务: http://localhost:5173
echo API 文档: http://localhost:8000/docs
echo ========================================
echo.
echo 按任意键返回主菜单...
pause >nul
goto menu

REM ========================================
REM Docker 部署模式
REM ========================================
:docker_menu
cls
echo ========================================
echo Docker 部署模式
echo ========================================
echo.
echo [1] 启动服务
echo [2] 停止服务
echo [3] 重启服务
echo [4] 查看日志
echo [0] 返回主菜单
echo.
set /p docker_choice="请输入选项 (0-4): "

if "%docker_choice%"=="1" goto docker_start
if "%docker_choice%"=="2" goto docker_stop
if "%docker_choice%"=="3" goto docker_restart
if "%docker_choice%"=="4" goto docker_logs
if "%docker_choice%"=="0" goto menu
goto docker_menu

:docker_start
echo.
echo [INFO] 检查 Docker...
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker 未安装，请先安装 Docker Desktop
    pause
    goto docker_menu
)

where docker-compose >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose 未安装
    pause
    goto docker_menu
)

if not exist .env (
    echo [WARN] .env 文件不存在，从 .env.example 复制
    copy .env.example .env
    echo [WARN] 请编辑 .env 文件，配置必要的环境变量
    pause
)

echo [INFO] 启动 Docker 服务...
docker-compose up -d

echo [INFO] 等待服务启动...
timeout /t 10 /nobreak >nul

echo [INFO] 检查服务状态...
docker-compose ps

echo.
echo ========================================
echo Docker 服务已启动！
echo ========================================
echo 前端地址: http://localhost
echo 后端地址: http://localhost:8000
echo MinIO 控制台: http://localhost:9001
echo ========================================
pause
goto docker_menu

:docker_stop
echo.
echo [INFO] 停止 Docker 服务...
docker-compose down
echo [INFO] 服务已停止
pause
goto docker_menu

:docker_restart
echo.
echo [INFO] 重启 Docker 服务...
docker-compose restart
echo [INFO] 服务已重启
pause
goto docker_menu

:docker_logs
echo.
echo [INFO] 查看日志 (按 Ctrl+C 退出)...
docker-compose logs -f
pause
goto docker_menu

REM ========================================
REM 查看服务状态
REM ========================================
:status
cls
echo ========================================
echo 服务状态
echo ========================================
echo.

REM 检查 Docker 服务
echo [Docker 服务]
docker-compose ps 2>nul
if %errorlevel% neq 0 (
    echo Docker 服务未运行
)

echo.
echo [本地服务]
REM 检查后端
curl -f http://localhost:8000/api/v1/health/status >nul 2>&1
if %errorlevel% equ 0 (
    echo √ 后端服务正常 (http://localhost:8000)
) else (
    echo × 后端服务未运行
)

REM 检查前端
curl -f http://localhost:5173 >nul 2>&1
if %errorlevel% equ 0 (
    echo √ 前端服务正常 (http://localhost:5173)
) else (
    curl -f http://localhost >nul 2>&1
    if %errorlevel% equ 0 (
        echo √ 前端服务正常 (http://localhost)
    ) else (
        echo × 前端服务未运行
    )
)

echo.
echo ========================================
pause
goto menu

REM ========================================
REM 初始化数据库
REM ========================================
:init_db
cls
echo ========================================
echo 初始化数据库
echo ========================================
echo.

REM 检查是否使用 Docker
docker-compose ps | findstr "petition-backend" >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] 使用 Docker 初始化...
    docker-compose exec backend python manual_create_tables.py
    docker-compose exec backend python init_standard_templates.py
) else (
    echo [INFO] 使用本地环境初始化...
    cd backend
    call venv\Scripts\activate
    python manual_create_tables.py
    python init_standard_templates.py
    cd ..
)

echo.
echo [INFO] 数据库初始化完成
pause
goto menu

REM ========================================
REM 备份数据
REM ========================================
:backup
cls
echo ========================================
echo 备份数据
echo ========================================
echo.

set BACKUP_DIR=backups\%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set BACKUP_DIR=%BACKUP_DIR: =0%
mkdir "%BACKUP_DIR%" 2>nul

echo [INFO] 备份数据到 %BACKUP_DIR%...

REM 检查是否使用 Docker
docker-compose ps | findstr "petition-postgres" >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] 备份 Docker 数据库...
    docker-compose exec -T postgres pg_dump -U postgres petition_system > "%BACKUP_DIR%\database.sql"
) else (
    echo [WARN] Docker 服务未运行，跳过备份
)

echo [INFO] 备份完成: %BACKUP_DIR%
pause
goto menu

REM ========================================
REM 清理数据
REM ========================================
:clean
cls
echo ========================================
echo 清理数据
echo ========================================
echo.
echo [WARN] 这将删除所有数据库、Redis 和 MinIO 数据！
echo.
set /p confirm="确定要继续吗？(yes/no): "

if /i "%confirm%"=="yes" (
    echo.
    echo [INFO] 清理 Docker 数据...
    docker-compose down -v
    echo [INFO] 数据已清理
) else (
    echo [INFO] 取消清理
)

pause
goto menu

REM ========================================
REM 退出
REM ========================================
:end
echo.
echo 感谢使用！
endlocal
exit /b 0
