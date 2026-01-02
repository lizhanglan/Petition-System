@echo off
echo ========================================
echo 信访智能文书生成系统启动脚本
echo ========================================
echo.

echo [1/2] 启动后端服务...
start "Backend Server" cmd /k "cd backend && python run.py"
timeout /t 3 /nobreak >nul

echo [2/2] 启动前端服务...
start "Frontend Server" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo 系统启动完成！
echo 后端服务: http://localhost:8000
echo 前端服务: http://localhost:5173
echo API 文档: http://localhost:8000/docs
echo ========================================
pause
