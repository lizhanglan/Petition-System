@echo off
echo ========================================
echo 重启后端服务（WPS配置更新）
echo ========================================
echo.

echo [1/3] 停止后端服务...
taskkill /F /IM python.exe /T >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ 后端服务已停止
) else (
    echo ! 没有找到运行中的Python进程
)

echo.
echo [2/3] 等待进程完全退出...
timeout /t 3 /nobreak >nul

echo.
echo [3/3] 启动后端服务...
cd backend
start "后端服务" cmd /k "python run.py"

echo.
echo ========================================
echo ✓ 后端服务重启完成！
echo ========================================
echo.
echo 请查看新打开的窗口中的日志
echo 应该看到: [PreviewSelector] 尝试使用WPS服务...
echo.
pause
