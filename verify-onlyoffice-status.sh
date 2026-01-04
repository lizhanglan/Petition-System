#!/bin/bash

echo "=========================================="
echo "ONLYOFFICE 状态验证脚本"
echo "=========================================="
echo ""

echo "1. 检查前端容器代码更新状态..."
echo "----------------------------------------"
FRONTEND_CODE=$(docker exec petition-frontend sh -c 'cat /usr/share/nginx/html/assets/*.js 2>/dev/null | grep -o "Loading API script" | head -1')
if [ "$FRONTEND_CODE" = "Loading API script" ]; then
    echo "✅ 前端代码已更新（包含最新的ONLYOFFICE加载逻辑）"
else
    echo "❌ 前端代码未更新"
fi
echo ""

echo "2. 检查前端Nginx配置..."
echo "----------------------------------------"
NGINX_CONFIG=$(docker exec petition-frontend cat /etc/nginx/conf.d/default.conf | grep -A 2 'location ~\* \\.\(js\|css\)' | grep 'no-cache')
if [ -n "$NGINX_CONFIG" ]; then
    echo "✅ Nginx配置正确（JS文件使用no-cache）"
else
    echo "❌ Nginx配置可能有问题"
fi
echo ""

echo "3. 检查后端容器代码状态..."
echo "----------------------------------------"
BACKEND_CODE=$(docker exec petition-backend grep -n 'methods=\["GET", "HEAD"\]' /app/app/api/v1/endpoints/onlyoffice.py | head -1)
if [ -n "$BACKEND_CODE" ]; then
    echo "✅ 后端代码已更新（支持HEAD请求）"
    echo "   $BACKEND_CODE"
else
    echo "❌ 后端代码未更新"
fi
echo ""

echo "4. 测试后端HEAD请求..."
echo "----------------------------------------"
HEAD_RESPONSE=$(curl -I http://101.37.24.171:8000/api/v1/onlyoffice/download/file/1 2>/dev/null | head -1)
if [[ "$HEAD_RESPONSE" == *"200"* ]]; then
    echo "✅ 后端HEAD请求正常"
    echo "   $HEAD_RESPONSE"
else
    echo "❌ 后端HEAD请求失败"
    echo "   $HEAD_RESPONSE"
fi
echo ""

echo "5. 检查后端最近日志..."
echo "----------------------------------------"
echo "最近的ONLYOFFICE配置请求："
docker logs petition-backend --tail 20 | grep -E "(Generated file URL|config)" | tail -3
echo ""

echo "6. 检查ONLYOFFICE服务器状态..."
echo "----------------------------------------"
ONLYOFFICE_STATUS=$(curl -s http://101.37.24.171:9090/healthcheck 2>/dev/null)
if [ -n "$ONLYOFFICE_STATUS" ]; then
    echo "✅ ONLYOFFICE服务器运行正常"
else
    echo "⚠️  无法访问ONLYOFFICE健康检查端点"
fi
echo ""

echo "7. 检查容器运行状态..."
echo "----------------------------------------"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(petition|gracious)"
echo ""

echo "=========================================="
echo "验证完成"
echo "=========================================="
echo ""
echo "📋 下一步操作："
echo ""
echo "如果所有检查都通过（✅），问题在于浏览器缓存："
echo ""
echo "1. 打开浏览器开发者工具（F12）"
echo "2. 按 Ctrl+Shift+Delete 清除缓存"
echo "3. 选择'过去1小时'，勾选'缓存的图片和文件'"
echo "4. 点击'清除数据'"
echo "5. 完全关闭浏览器，重新打开"
echo "6. 访问 http://101.37.24.171:8081"
echo ""
echo "或者使用硬刷新："
echo "- Windows/Linux: Ctrl + Shift + R"
echo "- Mac: Cmd + Shift + R"
echo ""
echo "详细说明请查看："
echo "docs/troubleshooting/ONLYOFFICE浏览器缓存清除完整方案.md"
echo ""
