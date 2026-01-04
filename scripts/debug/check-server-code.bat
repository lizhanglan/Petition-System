@echo off
echo ==========================================
echo 检查服务器上的代码是否已更新
echo ==========================================
echo.

echo 1. 检查服务器上宿主机代码（~/lizhanglan/Petition-System）
echo -------------------------------------------
ssh root@101.37.24.171 "cd ~/lizhanglan/Petition-System && echo 'Git最新提交：' && git log -1 --oneline && echo. && echo '检查 onlyoffice.py 中的 HEAD 方法支持：' && grep -n '@router.api_route' backend/app/api/v1/endpoints/onlyoffice.py && echo. && echo '检查第105行附近的代码：' && sed -n '103,107p' backend/app/api/v1/endpoints/onlyoffice.py && echo. && echo '检查第194行附近的代码：' && sed -n '192,196p' backend/app/api/v1/endpoints/onlyoffice.py"

echo.
echo ==========================================
echo 2. 检查容器内运行的代码
echo -------------------------------------------
ssh root@101.37.24.171 "echo '检查后端容器内的代码：' && docker exec petition-backend grep -n '@router.api_route' /app/app/api/v1/endpoints/onlyoffice.py && echo. && echo '检查容器内第105行附近的代码：' && docker exec petition-backend sed -n '103,107p' /app/app/api/v1/endpoints/onlyoffice.py && echo. && echo '检查容器内第194行附近的代码：' && docker exec petition-backend sed -n '192,196p' /app/app/api/v1/endpoints/onlyoffice.py"

echo.
echo ==========================================
echo 3. 对比结果
echo -------------------------------------------
echo 如果宿主机代码显示 methods=["GET", "HEAD"]
echo 但容器内代码显示 methods=["GET"] 或没有HEAD
echo 说明容器内代码是旧的，需要重启容器
echo.
echo 解决方案：ssh root@101.37.24.171 "cd ~/lizhanglan/Petition-System && docker-compose restart backend"
echo ==========================================
pause
