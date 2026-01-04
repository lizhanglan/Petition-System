@echo off
chcp 65001 >nul
echo ==========================================
echo 推送代码并触发服务器重建
echo ==========================================
echo.

echo 1. 检查本地代码状态...
git status
echo.

echo 2. 推送到GitHub...
git push origin main
if %errorlevel% neq 0 (
    echo 推送失败！请检查网络连接或Git配置
    pause
    exit /b 1
)
echo.

echo 3. 等待GitHub Actions完成...
echo    请访问 https://github.com/你的用户名/petition_system/actions 查看进度
echo    等待约2-3分钟后，继续下一步
echo.
pause

echo 4. 完成！
echo.
echo 接下来需要在服务器上执行以下命令：
echo.
echo    cd ~/lizhanglan/petition_system
echo    chmod +x force-rebuild-frontend.sh
echo    ./force-rebuild-frontend.sh
echo.
echo 或者手动执行：
echo.
echo    docker-compose stop frontend
echo    docker-compose rm -f frontend
echo    docker rmi petition_system-frontend
echo    docker builder prune -af
echo    docker-compose build --no-cache --build-arg CACHEBUST=$(date +%%s) frontend
echo    docker-compose up -d frontend
echo.
pause
