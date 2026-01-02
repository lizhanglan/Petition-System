@echo off
REM 信访智能文书生成系统 - Docker 部署脚本 (Windows)
REM 使用方法: deploy.bat [start|stop|restart|logs|status|init|backup|clean]

setlocal enabledelayedexpansion

REM 检查 Docker 是否安装
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker 未安装，请先安装 Docker Desktop
    exit /b 1
)

where docker-compose >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose 未安装，请先安装 Docker Compose
    exit /b 1
)

REM 检查环境变量文件
if not exist .env (
    echo [WARN] .env 文件不存在，从 .env.example 复制
    copy .env.example .env
    echo [WARN] 请编辑 .env 文件，配置必要的环境变量（特别是 DEEPSEEK_API_KEY）
    pause
)

REM 获取命令参数
set COMMAND=%1
if "%COMMAND%"=="" set COMMAND=start

REM 执行命令
if "%COMMAND%"=="start" goto start
if "%COMMAND%"=="stop" goto stop
if "%COMMAND%"=="restart" goto restart
if "%COMMAND%"=="logs" goto logs
if "%COMMAND%"=="status" goto status
if "%COMMAND%"=="init" goto init
if "%COMMAND%"=="backup" goto backup
if "%COMMAND%"=="clean" goto clean
goto usage

:start
echo [INFO] 启动服务...
docker-compose up -d
if %errorlevel% neq 0 (
    echo [ERROR] 启动失败
    exit /b 1
)
echo [INFO] 等待服务启动...
timeout /t 10 /nobreak >nul
echo [INFO] 检查服务状态...
docker-compose ps
echo.
echo [INFO] 服务已启动！
echo [INFO] 前端地址: http://localhost
echo [INFO] 后端地址: http://localhost:8000
echo [INFO] MinIO 控制台: http://localhost:9001
goto end

:stop
echo [INFO] 停止服务...
docker-compose down
echo [INFO] 服务已停止
goto end

:restart
echo [INFO] 重启服务...
docker-compose restart
echo [INFO] 服务已重启
goto end

:logs
if "%2"=="" (
    docker-compose logs -f
) else (
    docker-compose logs -f %2
)
goto end

:status
echo [INFO] 服务状态:
docker-compose ps
echo.
echo [INFO] 健康检查:
curl -f http://localhost:8000/api/v1/health/status >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] √ 后端服务正常
) else (
    echo [ERROR] × 后端服务异常
)
curl -f http://localhost >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] √ 前端服务正常
) else (
    echo [ERROR] × 前端服务异常
)
goto end

:init
echo [INFO] 初始化数据库...
docker-compose exec backend python manual_create_tables.py
docker-compose exec backend python init_standard_templates.py
echo [INFO] 数据库初始化完成
goto end

:backup
set BACKUP_DIR=backups\%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set BACKUP_DIR=%BACKUP_DIR: =0%
mkdir "%BACKUP_DIR%" 2>nul
echo [INFO] 备份数据到 %BACKUP_DIR%...
docker-compose exec -T postgres pg_dump -U postgres petition_system > "%BACKUP_DIR%\database.sql"
echo [INFO] 备份完成
goto end

:clean
set /p CONFIRM="确定要清理所有数据吗？这将删除数据库、Redis 和 MinIO 的所有数据！(yes/no): "
if /i "%CONFIRM%"=="yes" (
    echo [WARN] 清理数据...
    docker-compose down -v
    echo [INFO] 数据已清理
) else (
    echo [INFO] 取消清理
)
goto end

:usage
echo 使用方法: %0 {start^|stop^|restart^|logs^|status^|init^|backup^|clean}
echo.
echo 命令说明:
echo   start   - 启动所有服务
echo   stop    - 停止所有服务
echo   restart - 重启所有服务
echo   logs    - 查看日志 (可选: logs ^<service^>)
echo   status  - 查看服务状态
echo   init    - 初始化数据库
echo   backup  - 备份数据
echo   clean   - 清理所有数据
exit /b 1

:end
endlocal
