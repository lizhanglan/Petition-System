@echo off
echo ==========================================
echo 检查容器热更新支持状态
echo ==========================================
echo.

echo 1. 检查后端容器挂载
echo -------------------------------------------
ssh root@101.37.24.171 "docker inspect petition-backend | grep -A 20 Mounts"

echo.
echo 2. 检查前端容器挂载
echo -------------------------------------------
ssh root@101.37.24.171 "docker inspect petition-frontend | grep -A 20 Mounts"

echo.
echo ==========================================
echo 分析结果：
echo ==========================================
echo 后端：
echo   - 如果看到 /app/app 挂载 = 支持热更新（修改代码后重启容器即可）
echo   - 如果没有 /app/app 挂载 = 不支持热更新（需要重新构建镜像）
echo.
echo 前端：
echo   - Mounts: [] = 不支持热更新（需要重新构建镜像）
echo   - 前端是编译型应用，生产环境不建议热更新
echo ==========================================
pause
