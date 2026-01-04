#!/bin/bash
# 检查 Docker 容器内的代码是否已更新

echo "=========================================="
echo "检查 Docker 容器内的代码更新状态"
echo "=========================================="
echo ""

echo "1️⃣ 检查容器是否运行..."
docker ps | grep petition-backend
echo ""

echo "2️⃣ 检查 deepseek_service.py 的关键修改..."
echo "查找 'document_content: 完整的文书正文内容，按照公文格式编排' 这行..."
docker exec petition-backend grep -n "按照公文格式编排" /app/app/services/deepseek_service.py
echo ""

echo "3️⃣ 检查完整的 system_prompt 内容..."
docker exec petition-backend cat /app/app/services/deepseek_service.py | grep -A 30 "async def generate_document" | head -40
echo ""

echo "4️⃣ 检查文件最后修改时间..."
docker exec petition-backend stat /app/app/services/deepseek_service.py | grep Modify
echo ""

echo "5️⃣ 检查 Git 提交记录..."
git log --oneline -1
echo ""

echo "6️⃣ 对比关键代码片段..."
echo "容器内的代码："
docker exec petition-backend grep -A 5 "document_content.*完整的文书正文" /app/app/services/deepseek_service.py
echo ""

echo "=========================================="
echo "检查完成！"
echo "=========================================="
