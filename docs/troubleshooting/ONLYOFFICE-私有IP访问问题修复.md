# ONLYOFFICE私有IP访问问题修复

## 问题描述

文件预览失败，ONLYOFFICE报错：
```
errorCode: -4
errorDescription: '下载失败'
```

后端日志显示只收到file/1的配置请求，没有收到其他文件的下载请求。

## 根本原因

ONLYOFFICE日志显示：
```
Error: DNS lookup 172.18.0.4(family:4, host:petition-backend) is not allowed. 
Because, It is private IP address.
```

虽然配置文件 `/etc/onlyoffice/documentserver/local.json` 已经正确设置了 `allowPrivateIPAddress: true`，但是 **docservice 和 converter 进程没有重新加载配置**，仍在使用旧配置拒绝访问私有IP。

## 解决方案

### 1. 重启ONLYOFFICE服务进程

```bash
# 重启docservice和converter进程
docker exec gracious_curran supervisorctl restart ds:docservice ds:converter

# 验证进程状态
docker exec gracious_curran supervisorctl status
```

预期输出：
```
ds:converter     RUNNING   pid 10258, uptime 0:01:10
ds:docservice    RUNNING   pid 10246, uptime 0:01:11
```

### 2. 验证配置已加载

```bash
# 检查配置文件
docker exec gracious_curran cat /etc/onlyoffice/documentserver/local.json
```

应该包含：
```json
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
      },
      "request-filtering-agent": {
        "allowPrivateIPAddress": true,
        "allowMetaIPAddress": true
      }
    }
  }
}
```

### 3. 测试网络连接

```bash
# 测试ONLYOFFICE容器能否访问后端
docker exec gracious_curran curl -I http://petition-backend:8000/api/v1/onlyoffice/download/file/2

# 测试文件下载
docker exec gracious_curran curl -s http://petition-backend:8000/api/v1/onlyoffice/download/file/2 | wc -c
```

预期：
- HEAD请求返回 `HTTP/1.1 200 OK`
- 文件下载成功，返回字节数

## 验证步骤

1. 打开浏览器（建议使用无痕模式）
2. 访问：http://101.37.24.171:8081
3. 登录系统
4. 进入"文件研判"页面
5. 点击任意文件的"预览"按钮

预期结果：
- ONLYOFFICE编辑器正常加载
- 文档内容正常显示
- 没有错误提示

## 技术细节

### 问题时间线

1. **11:29-11:33** - ONLYOFFICE日志显示私有IP错误（旧配置）
2. **11:46** - 重启docservice和converter进程
3. **11:48** - 测试成功，可以访问后端并下载文件

### 关键配置

- **ONLYOFFICE容器**: gracious_curran (172.18.0.6)
- **后端容器**: petition-backend (172.18.0.4)
- **Docker网络**: petition-system_petition-network
- **后端URL**: http://petition-backend:8000 (Docker内部网络)

### 为什么需要重启进程

ONLYOFFICE DocumentServer的配置文件修改后，需要重启相关服务进程才能生效：
- `ds:docservice` - 文档服务，处理文档编辑
- `ds:converter` - 转换服务，处理文档格式转换

仅重启容器（`docker restart`）不够，因为容器启动脚本可能不会重新加载配置。使用 `supervisorctl restart` 可以确保进程重新读取配置文件。

## 相关文件

- 配置文件：`/etc/onlyoffice/documentserver/local.json`（容器内）
- 后端服务：`backend/app/services/onlyoffice_service.py`
- 后端API：`backend/app/api/v1/endpoints/onlyoffice.py`
- 前端组件：`frontend/src/components/OnlyOfficeEditor.vue`

## 修复日期

2026-01-04

## 状态

✅ 已修复并验证
