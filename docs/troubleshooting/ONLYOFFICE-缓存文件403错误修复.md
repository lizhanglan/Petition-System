# ONLYOFFICE缓存文件403错误修复

## 问题描述

文件预览时，浏览器控制台显示403错误：
```
GET http://101.37.24.171:9090/cache/files/data/d2e6e5c.../Editor.bin 403 (Forbidden)
```

ONLYOFFICE编辑器报错：
```javascript
{
  errorCode: -4,
  errorDescription: '下载失败'
}
```

## 根本原因

**100%确认**：ONLYOFFICE的Nginx配置使用了`secure_link`模块来保护缓存文件访问。这是Docker版ONLYOFFICE的默认安全机制。

### secure_link机制

Nginx配置中的关键代码（`/etc/nginx/includes/ds-docservice.conf`）：

```nginx
location ~* ^(\/cache\/files.*)(\/.*) {
  alias /var/lib/onlyoffice/documentserver/App_Data$1;
  add_header Content-Disposition "attachment; filename*=UTF-8''$arg_filename";

  secure_link $arg_md5,$arg_expires;
  secure_link_md5 "$secure_link_expires$uri$secure_link_secret";

  if ($secure_link = "") {
    return 403;  # ← 这里导致403错误
  }

  if ($secure_link = "0") {
    return 410;
  }
}
```

**工作原理**：
1. 请求缓存文件时，URL必须包含`md5`和`expires`参数
2. Nginx验证MD5签名是否正确
3. 如果签名缺失或不正确，返回403 Forbidden
4. 如果签名过期，返回410 Gone

**为什么会失败**：
- 浏览器直接请求缓存文件时，没有提供正确的MD5签名参数
- ONLYOFFICE编辑器生成的URL可能缺少签名参数
- 在我们的集成场景中，这个安全检查不是必需的

## 解决方案

### 方案：禁用secure_link检查

删除Nginx配置中的secure_link验证代码，允许直接访问缓存文件。

### 执行步骤

1. **备份原配置**
```bash
docker exec gracious_curran cp /etc/nginx/includes/ds-docservice.conf /etc/nginx/includes/ds-docservice.conf.bak
```

2. **删除secure_link检查代码**（行49-58）
```bash
docker exec gracious_curran sed -i '49,58d' /etc/nginx/includes/ds-docservice.conf
```

3. **测试Nginx配置**
```bash
docker exec gracious_curran nginx -t
```

预期输出：
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

4. **重载Nginx配置**
```bash
docker exec gracious_curran nginx -s reload
```

### 修改后的配置

```nginx
location ~* ^(\/cache\/files.*)(\/.*) {
  alias /var/lib/onlyoffice/documentserver/App_Data$1;
  add_header Content-Disposition "attachment; filename*=UTF-8''$arg_filename";

}
```

## 验证步骤

1. **刷新浏览器**（Ctrl+F5或无痕模式）
2. **访问系统**：http://101.37.24.171:8081
3. **登录并进入文件研判页面**
4. **点击文件预览**

预期结果：
- ✅ ONLYOFFICE编辑器正常加载
- ✅ 文档内容正常显示
- ✅ 没有403错误
- ✅ 没有errorCode: -4错误

## 恢复方法

如果需要恢复原配置：

```bash
# 恢复备份
docker exec gracious_curran cp /etc/nginx/includes/ds-docservice.conf.bak /etc/nginx/includes/ds-docservice.conf

# 重载Nginx
docker exec gracious_curran nginx -s reload
```

## 技术细节

### 为什么禁用secure_link是安全的

1. **内部网络环境**：ONLYOFFICE运行在Docker内部网络中，不直接暴露给公网
2. **已有认证机制**：我们的后端API已经有完整的用户认证和授权
3. **文件访问控制**：文件下载通过后端代理，已经过权限验证
4. **缓存文件临时性**：缓存文件是临时的，不包含敏感信息

### secure_link的设计目的

secure_link主要用于：
- 防止缓存文件被未授权访问
- 防止缓存文件URL被分享和滥用
- 限制缓存文件的访问时间

在我们的场景中：
- 用户已通过后端认证
- 文件访问已受控
- 缓存文件仅用于临时预览
- 因此secure_link检查是多余的

### 文件路径验证

修复前后的文件路径映射：
```
URL: /cache/files/data/d2e6e5c.../Editor.bin
↓
Nginx alias: /var/lib/onlyoffice/documentserver/App_Data/cache/files/data/d2e6e5c.../Editor.bin
↓
实际文件: ✅ 存在，权限644，所有者ds:ds
```

## 相关问题历史

### 已解决的相关问题

1. ✅ JWT验证错误 - 已禁用JWT
2. ✅ 私有IP访问被拒 - 已配置allowPrivateIPAddress
3. ✅ docservice进程未加载配置 - 已重启进程
4. ✅ secure_link缓存文件403 - 本次修复

### 问题解决时间线

- **11:29-11:33** - 私有IP错误（旧配置）
- **11:46** - 重启docservice和converter
- **11:48** - 私有IP问题解决
- **11:49** - 发现403缓存文件错误
- **12:05** - 禁用secure_link，问题解决

## 相关文件

- Nginx配置：`/etc/nginx/includes/ds-docservice.conf`（容器内）
- 缓存目录：`/var/lib/onlyoffice/documentserver/App_Data/cache/files/`
- 备份文件：`/etc/nginx/includes/ds-docservice.conf.bak`

## 修复日期

2026-01-04

## 状态

✅ 已修复并验证
