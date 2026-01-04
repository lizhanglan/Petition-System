#!/bin/bash
# 在服务器上执行的命令序列

echo "=========================================="
echo "应用后端热更新配置并修复ONLYOFFICE"
echo "=========================================="
echo ""

# 1. 进入项目目录
cd ~/lizhanglan/Petition-System

# 2. 拉取最新代码（包含docker-compose.yml的挂载配置）
echo "1. 拉取最新代码..."
git pull origin main

# 3. 查看当前docker-compose.yml中的后端挂载配置
echo ""
echo "2. 检查docker-compose.yml中的后端挂载配置..."
grep -A 5 "backend/app:/app/app" docker-compose.yml

# 4. 停止并删除后端容器
echo ""
echo "3. 停止并删除后端容器..."
docker-compose stop backend
docker-compose rm -f backend

# 5. 重新创建后端容器（应用新的挂载配置）
echo ""
echo "4. 重新创建后端容器（应用新挂载）..."
docker-compose up -d backend

# 6. 等待容器启动
echo ""
echo "5. 等待容器启动（15秒）..."
sleep 15

# 7. 检查容器状态
echo ""
echo "6. 检查容器状态..."
docker ps | grep petition-backend

# 8. 验证挂载配置
echo ""
echo "7. 验证挂载配置..."
docker inspect petition-backend --format='{{json .Mounts}}' | python3 -m json.tool | grep -B 2 -A 3 "/app/app"

# 9. 验证代码是否包含HEAD方法
echo ""
echo "8. 验证代码是否包含HEAD方法..."
docker exec petition-backend grep -n "methods=" /app/app/api/v1/endpoints/onlyoffice.py | head -2

# 10. 测试HEAD请求
echo ""
echo "9. 测试HEAD请求..."
curl -I http://101.37.24.171:8000/api/v1/onlyoffice/download/file/1 2>&1 | head -10

# 11. 查看后端日志（最后20行）
echo ""
echo "10. 查看后端日志..."
docker logs petition-backend --tail 20

echo ""
echo "=========================================="
echo "完成！"
echo "=========================================="
echo ""
echo "验证结果："
echo "  ✓ 如果看到 /app/app 挂载 → 热更新已启用"
echo "  ✓ 如果看到 methods=[\"GET\", \"HEAD\"] → 代码已更新"
echo "  ✓ 如果 HEAD 请求返回 200 OK → 功能正常"
echo ""
echo "下次修改后端代码后，只需："
echo "  1. 本地推送到GitHub"
echo "  2. 服务器上: cd ~/lizhanglan/Petition-System && git pull"
echo "  3. 重启容器: docker-compose restart backend"
echo "=========================================="
