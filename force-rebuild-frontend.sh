#!/bin/bash

# 强制重新构建前端的脚本
# 用于解决Docker缓存导致的代码更新问题

echo "=========================================="
echo "强制重新构建前端容器"
echo "=========================================="

# 1. 停止并删除前端容器
echo "1. 停止并删除前端容器..."
docker-compose stop frontend
docker-compose rm -f frontend

# 2. 删除前端镜像
echo "2. 删除前端镜像..."
docker rmi petition_system-frontend || true

# 3. 清理所有构建缓存
echo "3. 清理所有构建缓存..."
docker builder prune -af

# 4. 使用CACHEBUST参数重新构建前端
echo "4. 重新构建前端（使用时间戳破坏缓存）..."
docker-compose build --no-cache --build-arg CACHEBUST=$(date +%s) frontend

# 5. 启动前端容器
echo "5. 启动前端容器..."
docker-compose up -d frontend

# 6. 等待容器启动
echo "6. 等待容器启动..."
sleep 5

# 7. 验证构建结果
echo "7. 验证构建结果..."
echo "检查容器状态："
docker-compose ps frontend

echo ""
echo "检查前端文件大小："
docker exec petition-frontend sh -c "ls -lh /usr/share/nginx/html/assets/OnlyOfficeEditor-*.js"

echo ""
echo "检查文件内容（前500字符）："
docker exec petition-frontend sh -c "head -c 500 /usr/share/nginx/html/assets/OnlyOfficeEditor-*.js"

echo ""
echo "=========================================="
echo "重新构建完成！"
echo "=========================================="
echo ""
echo "请执行以下步骤验证："
echo "1. 清除浏览器缓存（Ctrl+Shift+Delete）"
echo "2. 访问 http://101.37.24.171:8081"
echo "3. 打开开发者工具，查看控制台输出"
echo "4. 应该看到：[OnlyOffice] Editor config: {document: {...}, ...}"
echo "5. 不应该看到：undefined"
echo ""
