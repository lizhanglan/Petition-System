# ONLYOFFICE问题排查手册

**文档版本**: 1.0  
**更新日期**: 2026-01-04  
**适用版本**: ONLYOFFICE DocumentServer 9.2.1

---

## 目录

1. [快速诊断](#快速诊断)
2. [常见问题](#常见问题)
3. [错误代码对照表](#错误代码对照表)
4. [详细排查步骤](#详细排查步骤)
5. [日志分析](#日志分析)
6. [紧急恢复](#紧急恢复)

---

## 快速诊断

### 一键检查脚本

```bash
#!/bin/bash
echo "========== ONLYOFFICE 快速诊断 =========="

# 1. 检查容器状态
echo "1. 容器状态："
docker ps | grep gracious_curran

# 2. 检查进程状态
echo -e "\n2. 服务进程："
docker exec gracious_curran supervisorctl status | grep -E 'docservice|converter'

# 3. 检查配置
echo -e "\n3. JWT配置："
docker exec gracious_curran cat /etc/onlyoffice/documentserver/local.json | grep -A 10 "token"

# 4. 检查网络
echo -e "\n4. 网络连接："
docker exec gracious_curran curl -I http://petition-backend:8000/api/v1/onlyoffice/health 2>&1 | head -1

# 5. 检查最新错误
echo -e "\n5. 最新错误："
docker logs --tail 20 gracious_curran 2>&1 | grep -i error | tail -5

echo -e "\n========== 诊断完成 =========="
```

### 健康检查清单

| 检查项 | 命令 | 预期结果 |
|--------|------|----------|
| 容器运行 | `docker ps \| grep gracious_curran` | Up状态 |
| docservice | `docker exec gracious_curran supervisorctl status \| grep docservice` | RUNNING |
| converter | `docker exec gracious_curran supervisorctl status \| grep converter` | RUNNING |
| 端口监听 | `curl -I http://101.37.24.171:9090` | 200 OK |
| 后端连接 | `docker exec gracious_curran curl -I http://petition-backend:8000` | 200 OK |

---

## 常见问题

### 问题1：编辑器无法加载

**症状**：
- 页面一直显示"正在加载编辑器..."
- 浏览器控制台无错误

**可能原因**：
1. ONLYOFFICE服务未启动
2. API脚本加载失败
3. 网络连接问题

**排查步骤**：

```bash
# 1. 检查ONLYOFFICE服务
docker ps | grep gracious_curran
docker exec gracious_curran supervisorctl status

# 2. 测试API脚本
curl -I http://101.37.24.171:9090/web-apps/apps/api/documents/api.js

# 3. 检查浏览器网络面板
# F12 → Network → 查看api.js是否加载成功
```

**解决方案**：

```bash
# 重启ONLYOFFICE服务
docker restart gracious_curran

# 或只重启服务进程
docker exec gracious_curran supervisorctl restart ds:docservice ds:converter
```

---

### 问题2：errorCode: -4 (下载失败)

**症状**：
- 编辑器显示错误：errorCode: -4, errorDescription: '下载失败'
- ONLYOFFICE无法下载文件

**可能原因**：
1. 后端下载端点不可访问
2. 文件不存在或权限问题
3. 网络连接问题

**排查步骤**：

```bash
# 1. 检查后端是否收到请求
docker logs --tail 50 petition-backend | grep "onlyoffice/download"

# 2. 测试ONLYOFFICE能否访问后端
docker exec gracious_curran curl -v http://petition-backend:8000/api/v1/onlyoffice/download/file/1

# 3. 检查文件是否存在
# 在后端日志中查看文件ID和storage_path
```

**解决方案**：

```bash
# 如果是网络问题，检查Docker网络
docker network inspect petition-system_petition-network

# 如果ONLYOFFICE不在网络中，加入网络
docker network connect petition-system_petition-network gracious_curran

# 重启后端容器
docker-compose restart petition-backend
```

---

### 问题3：errorCode: -20 (JWT验证失败)

**症状**：
- 编辑器显示错误：errorCode: -20
- 日志显示JWT验证失败

**原因**：
JWT验证未正确禁用

**解决方案**：

```bash
# 1. 创建配置文件禁用JWT
docker exec gracious_curran bash -c 'cat > /etc/onlyoffice/documentserver/local.json << EOF
{
  "services": {
    "CoAuthoring": {
      "token": {
        "enable": {
          "request": {
            "inbox": false,
            "outbox": false
          },
          "browser": false
        }
      }
    }
  }
}
EOF'

# 2. 重启服务进程
docker exec gracious_curran supervisorctl restart ds:docservice ds:converter

# 3. 验证配置
docker exec gracious_curran cat /etc/onlyoffice/documentserver/local.json
```

---

### 问题4：私有IP访问被拒

**症状**：
- 日志显示：DNS lookup 172.18.0.4 is not allowed. Because, It is private IP address.

**原因**：
ONLYOFFICE默认拒绝访问私有IP地址

**解决方案**：

```bash
# 1. 更新配置文件
docker exec gracious_curran bash -c 'cat > /etc/onlyoffice/documentserver/local.json << EOF
{
  "services": {
    "CoAuthoring": {
      "token": {
        "enable": {
          "request": {"inbox": false, "outbox": false},
          "browser": false
        }
      },
      "request-filtering-agent": {
        "allowPrivateIPAddress": true,
        "allowMetaIPAddress": true
      }
    }
  }
}
EOF'

# 2. 重启服务进程（重要！）
docker exec gracious_curran supervisorctl restart ds:docservice ds:converter

# 3. 等待5秒后测试
sleep 5
docker exec gracious_curran curl -I http://petition-backend:8000/api/v1/onlyoffice/download/file/1
```

---

### 问题5：缓存文件403错误

**症状**：
- 浏览器控制台显示：GET http://101.37.24.171:9090/cache/files/data/.../Editor.bin 403 (Forbidden)

**原因**：
Nginx的secure_link模块要求MD5签名

**解决方案**：

```bash
# 1. 备份配置
docker exec gracious_curran cp /etc/nginx/includes/ds-docservice.conf /etc/nginx/includes/ds-docservice.conf.bak

# 2. 删除secure_link检查代码（行49-58）
docker exec gracious_curran sed -i '49,58d' /etc/nginx/includes/ds-docservice.conf

# 3. 测试Nginx配置
docker exec gracious_curran nginx -t

# 4. 重载Nginx
docker exec gracious_curran nginx -s reload

# 5. 验证修改
docker exec gracious_curran sed -n '45,52p' /etc/nginx/includes/ds-docservice.conf
```

---

### 问题6：浏览器缓存问题

**症状**：
- 前端代码已更新，但浏览器仍使用旧代码
- 编辑器行为异常

**解决方案**：

```bash
# 方法1：强制刷新
# Ctrl + F5 (Windows/Linux)
# Cmd + Shift + R (Mac)

# 方法2：清除缓存
# F12 → Application → Clear storage → Clear site data

# 方法3：使用无痕模式
# Ctrl + Shift + N (Chrome)
# Ctrl + Shift + P (Firefox)

# 方法4：禁用缓存（开发时）
# F12 → Network → Disable cache
```

---

### 问题7：布局显示异常

**症状**：
- 编辑器显示区域太小
- 工具栏正常但文档内容区域不足

**原因**：
CSS布局问题，高度计算不正确

**解决方案**：

检查以下CSS属性：

```css
/* OnlyOfficeEditor组件 */
.onlyoffice-editor {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

#onlyoffice-editor {
  width: 100%;
  height: 100%;
  min-height: 500px;
}

/* 父容器 */
.preview-container {
  width: 100%;
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
}
```

---

### 问题8：HEAD请求失败

**症状**：
- 后端日志显示405 Method Not Allowed
- ONLYOFFICE发送HEAD请求失败

**原因**：
后端下载端点不支持HEAD方法

**解决方案**：

修改后端代码：

```python
@router.api_route("/download/file/{file_id}", methods=["GET", "HEAD"])
async def download_file_for_onlyoffice(file_id: int, request: Request, ...):
    # 如果是HEAD请求，只返回头部
    if request.method == "HEAD":
        return StreamingResponse(
            io.BytesIO(b""),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
        )
    
    # GET请求返回完整文件
    # ...
```

---

### 问题9：Docker网络隔离

**症状**：
- ONLYOFFICE无法访问后端
- 连接超时或拒绝连接

**排查步骤**：

```bash
# 1. 检查ONLYOFFICE是否在项目网络中
docker network inspect petition-system_petition-network | grep gracious_curran

# 2. 测试网络连接
docker exec gracious_curran ping petition-backend

# 3. 测试HTTP连接
docker exec gracious_curran curl -v http://petition-backend:8000
```

**解决方案**：

```bash
# 将ONLYOFFICE加入项目网络
docker network connect petition-system_petition-network gracious_curran

# 验证
docker network inspect petition-system_petition-network
```

---

### 问题10：插件下载卡住

**症状**：
- 容器启动时卡在"Installing plugins"
- 长时间无响应

**解决方案**：

```bash
# 方法1：跳过插件安装
docker run -d \
  --name gracious_curran \
  -p 9090:80 \
  -e JWT_ENABLED=false \
  -v /dev/null:/usr/bin/documentserver-pluginsmanager.sh \
  onlyoffice/documentserver

# 方法2：强制终止插件进程
docker exec gracious_curran pkill -f pluginsmanager
docker exec gracious_curran pkill -f wget
```

---

## 错误代码对照表

| 错误代码 | 描述 | 常见原因 | 解决方案 |
|---------|------|----------|----------|
| -1 | 未知错误 | 配置错误、网络问题 | 检查配置和日志 |
| -2 | 转换超时 | 文件太大、服务繁忙 | 增加超时时间 |
| -3 | 转换错误 | 文件格式不支持 | 检查文件格式 |
| -4 | 下载失败 | 文件URL不可访问 | 检查网络和URL |
| -5 | 文件损坏 | 文件内容错误 | 检查文件完整性 |
| -6 | 服务不可用 | ONLYOFFICE服务停止 | 重启服务 |
| -7 | 回调错误 | 回调URL不可访问 | 检查回调配置 |
| -20 | JWT验证失败 | JWT配置错误 | 禁用或配置JWT |

---

## 详细排查步骤

### 步骤1：检查服务状态

```bash
# 1. 检查容器
docker ps -a | grep gracious_curran

# 2. 检查进程
docker exec gracious_curran supervisorctl status

# 3. 检查端口
netstat -tlnp | grep 9090

# 4. 检查日志
docker logs --tail 100 gracious_curran
```

### 步骤2：检查网络连接

```bash
# 1. 从主机访问ONLYOFFICE
curl -I http://101.37.24.171:9090

# 2. 从ONLYOFFICE访问后端
docker exec gracious_curran curl -I http://petition-backend:8000

# 3. 从后端访问ONLYOFFICE
docker exec petition-backend curl -I http://gracious_curran:80

# 4. 检查DNS解析
docker exec gracious_curran nslookup petition-backend
```

### 步骤3：检查配置文件

```bash
# 1. JWT配置
docker exec gracious_curran cat /etc/onlyoffice/documentserver/local.json

# 2. Nginx配置
docker exec gracious_curran cat /etc/nginx/includes/ds-docservice.conf | grep -A 10 "cache/files"

# 3. 环境变量
docker exec gracious_curran env | grep -i jwt
```

### 步骤4：测试文件下载

```bash
# 1. 测试HEAD请求
curl -I http://101.37.24.171:8000/api/v1/onlyoffice/download/file/1

# 2. 测试GET请求
curl -o test.docx http://101.37.24.171:8000/api/v1/onlyoffice/download/file/1

# 3. 从ONLYOFFICE容器测试
docker exec gracious_curran curl -I http://petition-backend:8000/api/v1/onlyoffice/download/file/1
```

### 步骤5：查看详细日志

```bash
# 1. docservice日志
docker exec gracious_curran tail -f /var/log/onlyoffice/documentserver/docservice/out.log

# 2. converter日志
docker exec gracious_curran tail -f /var/log/onlyoffice/documentserver/converter/out.log

# 3. Nginx错误日志
docker exec gracious_curran tail -f /var/log/onlyoffice/documentserver/nginx.error.log

# 4. 后端日志
docker logs -f petition-backend | grep onlyoffice
```

---

## 日志分析

### 关键日志位置

| 日志类型 | 路径 | 说明 |
|---------|------|------|
| docservice | `/var/log/onlyoffice/documentserver/docservice/out.log` | 文档服务日志 |
| converter | `/var/log/onlyoffice/documentserver/converter/out.log` | 转换服务日志 |
| Nginx访问 | `/var/log/onlyoffice/documentserver/nginx.access.log` | 访问日志 |
| Nginx错误 | `/var/log/onlyoffice/documentserver/nginx.error.log` | 错误日志 |

### 常见日志模式

**成功的文件下载**：

```
[OnlyOffice] ========== Download Request ==========
[OnlyOffice] File ID: 1
[OnlyOffice] File found: test.docx
[OnlyOffice] SUCCESS: File downloaded from MinIO, size: 16876 bytes
INFO: 172.18.0.6:48282 - "GET /api/v1/onlyoffice/download/file/1 HTTP/1.1" 200 OK
```

**JWT验证错误**：

```
[ERROR] nodeJS - error: JWT verification failed
errorCode: -20
```

**私有IP错误**：

```
[ERROR] nodeJS - error downloadFile:url=http://petition-backend:8000/...
Error: DNS lookup 172.18.0.4(family:4, host:petition-backend) is not allowed. 
Because, It is private IP address.
```

**缓存文件403**：

```
GET /cache/files/data/d2e6e5c.../Editor.bin 403 (Forbidden)
```

### 日志过滤技巧

```bash
# 只看错误
docker logs gracious_curran 2>&1 | grep -i error

# 看特定时间段
docker logs --since 10m gracious_curran

# 实时监控错误
docker logs -f gracious_curran 2>&1 | grep -i error

# 统计错误数量
docker logs gracious_curran 2>&1 | grep -i error | wc -l
```

---

## 紧急恢复

### 场景1：服务完全无响应

```bash
# 1. 强制重启容器
docker restart gracious_curran

# 2. 等待30秒
sleep 30

# 3. 检查状态
docker exec gracious_curran supervisorctl status

# 4. 如果还不行，重新创建容器
docker stop gracious_curran
docker rm gracious_curran
docker run -d --name gracious_curran -p 9090:80 -e JWT_ENABLED=false onlyoffice/documentserver
docker network connect petition-system_petition-network gracious_curran
```

### 场景2：配置损坏

```bash
# 1. 恢复备份配置
docker exec gracious_curran cp /etc/onlyoffice/documentserver/local.json.bak /etc/onlyoffice/documentserver/local.json
docker exec gracious_curran cp /etc/nginx/includes/ds-docservice.conf.bak /etc/nginx/includes/ds-docservice.conf

# 2. 重启服务
docker exec gracious_curran supervisorctl restart ds:docservice ds:converter
docker exec gracious_curran nginx -s reload
```

### 场景3：数据库损坏

```bash
# 1. 停止服务
docker exec gracious_curran supervisorctl stop ds:docservice ds:converter

# 2. 重建数据库
docker exec gracious_curran sudo -u postgres psql -c "DROP DATABASE IF EXISTS onlyoffice;"
docker exec gracious_curran sudo -u postgres psql -c "CREATE DATABASE onlyoffice;"

# 3. 重启容器
docker restart gracious_curran
```

### 场景4：完全重新部署

```bash
# 1. 停止并删除容器
docker stop gracious_curran
docker rm gracious_curran

# 2. 清理数据（可选）
docker volume prune

# 3. 重新部署
docker run -d \
  --name gracious_curran \
  -p 9090:80 \
  -e JWT_ENABLED=false \
  onlyoffice/documentserver

# 4. 加入网络
docker network connect petition-system_petition-network gracious_curran

# 5. 重新配置
# （执行所有配置步骤）
```

---

## 预防措施

### 定期检查

```bash
# 每日检查脚本
#!/bin/bash
echo "$(date): ONLYOFFICE健康检查" >> /var/log/onlyoffice-health.log

# 检查服务状态
docker exec gracious_curran supervisorctl status | grep -E 'docservice|converter' >> /var/log/onlyoffice-health.log

# 检查错误日志
ERROR_COUNT=$(docker logs --since 24h gracious_curran 2>&1 | grep -i error | wc -l)
echo "24小时错误数: $ERROR_COUNT" >> /var/log/onlyoffice-health.log

# 如果错误过多，发送告警
if [ $ERROR_COUNT -gt 100 ]; then
    echo "警告：错误数量过多！" | mail -s "ONLYOFFICE告警" admin@example.com
fi
```

### 备份策略

```bash
# 每周备份配置
#!/bin/bash
BACKUP_DIR="/backup/onlyoffice/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# 备份配置文件
docker exec gracious_curran tar czf /tmp/config.tar.gz \
  /etc/onlyoffice/documentserver/ \
  /etc/nginx/includes/

docker cp gracious_curran:/tmp/config.tar.gz $BACKUP_DIR/

# 保留最近30天的备份
find /backup/onlyoffice/ -type d -mtime +30 -exec rm -rf {} \;
```

### 监控告警

```bash
# 使用cron定时检查
# crontab -e
*/5 * * * * /path/to/onlyoffice-health-check.sh
0 2 * * 0 /path/to/onlyoffice-backup.sh
```

---

## 联系支持

### 获取帮助

1. **查看官方文档**：https://api.onlyoffice.com/editors/troubleshooting
2. **社区论坛**：https://forum.onlyoffice.com/
3. **GitHub Issues**：https://github.com/ONLYOFFICE/DocumentServer/issues

### 提交问题时需要的信息

```bash
# 收集诊断信息
#!/bin/bash
echo "========== ONLYOFFICE诊断信息 =========="
echo "日期: $(date)"
echo ""

echo "1. 版本信息:"
docker exec gracious_curran cat /var/www/onlyoffice/documentserver/server/Common/sources/version.js | grep buildVersion

echo -e "\n2. 容器状态:"
docker ps | grep gracious_curran

echo -e "\n3. 进程状态:"
docker exec gracious_curran supervisorctl status

echo -e "\n4. 配置文件:"
docker exec gracious_curran cat /etc/onlyoffice/documentserver/local.json

echo -e "\n5. 最近错误:"
docker logs --tail 50 gracious_curran 2>&1 | grep -i error

echo -e "\n6. 网络测试:"
docker exec gracious_curran curl -I http://petition-backend:8000

echo "========== 诊断完成 =========="
```

---

**文档结束**
