@echo off
echo ==========================================
echo 部署带代码挂载的配置
echo ==========================================
echo.

echo 1. 等待GitHub Actions完成...
timeout /t 30

echo.
echo 2. 在服务器上拉取最新代码
ssh root@101.37.24.171 "cd ~/lizhanglan/Petition-System && git pull origin main"

echo.
echo 3. 停止并删除后端容器
ssh root@101.37.24.171 "cd ~/lizhanglan/Petition-System && docker-compose stop backend && docker-compose rm -f backend"

echo.
echo 4. 重新创建后端容器（使用新的挂载配置）
ssh root@101.37.24.171 "cd ~/lizhanglan/Petition-System && docker-compose up -d backend"

echo.
echo 5. 等待容器启动
timeout /t 10

echo.
echo 6. 检查容器状态
ssh root@101.37.24.171 "docker ps | grep petition-backend"

echo.
echo 7. 验证代码是否已挂载
ssh root@101.37.24.171 "docker exec petition-backend grep -n 'api_route' /app/app/api/v1/endpoints/onlyoffice.py | head -2"

echo.
echo 8. 测试HEAD请求
ssh root@101.37.24.171 "curl -I http://101.37.24.171:8000/api/v1/onlyoffice/download/file/1"

echo.
echo ==========================================
echo 部署完成！
echo ==========================================
pause
