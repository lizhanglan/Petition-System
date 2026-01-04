# ONLYOFFICE浏览器缓存清除完整方案

## 问题现象
- 前端代码已更新（容器内有最新代码）
- 后端正常返回配置
- 浏览器Network中**没有9090端口的请求**
- 编辑器一直显示"正在加载编辑器..."

## 根本原因
**浏览器使用了旧的JavaScript缓存**，即使Nginx配置了`no-cache`，浏览器仍可能使用磁盘缓存或Service Worker缓存。

## 解决方案

### 方案1：强制硬刷新（最快）⚡

1. **打开浏览器开发者工具**（F12）
2. **右键点击刷新按钮**，选择"清空缓存并硬性重新加载"
3. 或使用快捷键：
   - Windows/Linux: `Ctrl + Shift + R` 或 `Ctrl + F5`
   - Mac: `Cmd + Shift + R`

### 方案2：清除浏览器缓存（推荐）✅

#### Chrome/Edge
1. 按 `Ctrl + Shift + Delete`
2. 选择"时间范围"：**过去1小时**
3. 勾选：
   - ✅ 缓存的图片和文件
   - ✅ Cookie及其他网站数据（可选）
4. 点击"清除数据"
5. 关闭所有标签页，重新打开系统

#### Firefox
1. 按 `Ctrl + Shift + Delete`
2. 选择"时间范围"：**最近一小时**
3. 勾选：
   - ✅ 缓存
   - ✅ Cookie（可选）
4. 点击"立即清除"
5. 关闭所有标签页，重新打开系统

### 方案3：禁用缓存（开发调试用）🔧

1. 打开开发者工具（F12）
2. 切换到 **Network** 标签
3. 勾选 **Disable cache**
4. **保持开发者工具打开**
5. 刷新页面

### 方案4：隐私/无痕模式（临时测试）🕵️

1. 打开隐私/无痕窗口：
   - Chrome/Edge: `Ctrl + Shift + N`
   - Firefox: `Ctrl + Shift + P`
2. 访问系统：`http://101.37.24.171:8081`
3. 测试ONLYOFFICE功能

### 方案5：修改前端代码添加版本号（永久解决）🎯

修改 `frontend/vite.config.ts`，为构建文件添加时间戳：

```typescript
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        entryFileNames: `assets/[name]-[hash]-${Date.now()}.js`,
        chunkFileNames: `assets/[name]-[hash]-${Date.now()}.js`,
        assetFileNames: `assets/[name]-[hash]-${Date.now()}.[ext]`
      }
    }
  }
})
```

然后重新构建前端：
```bash
cd ~/lizhanglan/Petition-System
docker-compose stop frontend
docker-compose rm -f frontend
docker-compose build frontend --no-cache
docker-compose up -d frontend
```

## 验证步骤

清除缓存后，按以下步骤验证：

### 1. 检查浏览器Console
打开开发者工具（F12），切换到Console标签，应该看到：
```
[OnlyOffice] Loading API script...
[OnlyOffice] Creating script tag...
[OnlyOffice] Appending script to head...
[OnlyOffice] Script tag appended
[OnlyOffice] Script loaded successfully
[OnlyOffice] DocsAPI is ready
[OnlyOffice] Requesting config with: {file_id: 1, document_id: null, mode: "view"}
[OnlyOffice] Editor initialized
```

### 2. 检查Network标签
应该看到以下请求：
- ✅ `http://101.37.24.171:9090/web-apps/apps/api/documents/api.js` (200 OK)
- ✅ `POST http://101.37.24.171:8081/api/onlyoffice/config` (200 OK)
- ✅ `GET http://101.37.24.171:8000/api/v1/onlyoffice/download/file/1` (200 OK)
- ✅ 多个到 `101.37.24.171:9090` 的请求（ONLYOFFICE资源）

### 3. 检查后端日志
```bash
docker logs petition-backend --tail 50 | grep OnlyOffice
```

应该看到：
```
[OnlyOffice] Downloading from MinIO...
[OnlyOffice] SUCCESS: File downloaded from MinIO, size: XXXXX bytes
```

### 4. 检查ONLYOFFICE日志
```bash
docker exec gracious_curran tail -50 /var/log/onlyoffice/documentserver/docservice/out.log
```

应该看到文档加载日志。

## 当前状态确认

✅ **后端代码**：已更新并生效（HEAD请求正常）
✅ **前端代码**：已更新到容器（`Loading API script` 存在）
✅ **Nginx配置**：正确（JS文件使用`no-cache`）
❌ **浏览器缓存**：需要清除

## 下一步操作

**立即执行**：
1. 使用方案1或方案2清除浏览器缓存
2. 完全关闭浏览器，重新打开
3. 访问 `http://101.37.24.171:8081`
4. 登录后测试文件预览
5. 按照"验证步骤"检查是否成功

## 常见问题

### Q: 清除缓存后还是不行？
A: 尝试以下步骤：
1. 完全关闭浏览器（所有窗口）
2. 重新打开浏览器
3. 使用隐私/无痕模式测试
4. 尝试其他浏览器（Chrome/Firefox/Edge）

### Q: Network中还是没有9090请求？
A: 检查Console是否有JavaScript错误：
1. 打开开发者工具（F12）
2. 切换到Console标签
3. 查看是否有红色错误信息
4. 截图发送给我

### Q: 如何确认前端代码真的更新了？
A: 检查JavaScript文件内容：
```bash
docker exec petition-frontend sh -c 'cat /usr/share/nginx/html/assets/*.js 2>/dev/null | grep -o "Loading API script" | head -1'
```
如果输出 `Loading API script`，说明代码已更新。

## 技术说明

### 为什么会有缓存问题？
1. **浏览器磁盘缓存**：即使设置了`no-cache`，浏览器仍可能使用磁盘缓存
2. **Service Worker**：某些应用使用Service Worker缓存资源
3. **HTTP缓存头**：之前的强缓存头可能还在生效
4. **代理缓存**：中间代理服务器可能缓存了资源

### 为什么Nginx配置了no-cache还不够？
- `no-cache`只是告诉浏览器"需要验证"，但不是"不缓存"
- 浏览器可能因为各种原因跳过验证
- 硬刷新会强制浏览器忽略所有缓存

### 长期解决方案
1. **文件名哈希**：Vite已经为文件添加了哈希（如`OnlyOfficeEditor-BbNYYtGo.js`）
2. **版本号**：在HTML中添加版本号查询参数
3. **Service Worker**：正确配置Service Worker的缓存策略
4. **CDN**：使用CDN时配置正确的缓存策略
