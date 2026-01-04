# ONLYOFFICE修复检查清单

## 修复前检查 ✅

- [x] 问题确认：编辑器显示 "Editor config: undefined"
- [x] 根本原因：前端使用Axios响应对象而非响应数据
- [x] 次要问题：后端content_type字段不存在
- [x] 次要问题：中文文件名编码错误

## 代码修复 ✅

### 前端修复
- [x] `frontend/src/components/OnlyOfficeEditor.vue`
  - [x] 使用 `response.data` 获取配置
  - [x] 保留事件处理逻辑
  - [x] 保留错误处理

### 后端修复
- [x] `backend/app/api/v1/endpoints/onlyoffice.py`
  - [x] 添加MIME类型映射（替代content_type）
  - [x] 修复中文文件名编码（UTF-8）
  - [x] 添加详细调试日志
  - [x] 添加CORS头部
  - [x] 同时修复文件和文书下载端点

## 本地测试 ✅

- [x] 后端服务启动正常
- [x] 前端服务启动正常
- [x] 下载端点测试通过
  ```
  ✓ 成功! 状态码: 200, 大小: 189495 bytes
  ```
- [x] 后端日志显示正常
  ```
  [OnlyOffice] SUCCESS: File downloaded from MinIO, size: 189495 bytes
  ```

## 部署准备 ⏳

### 代码推送
- [ ] 暂存所有修改
  ```bash
  git add .
  ```
- [ ] 提交修改
  ```bash
  git commit -m "修复ONLYOFFICE编辑器加载问题"
  ```
- [ ] 推送到远程仓库
  ```bash
  git push origin main
  ```

### 服务器准备
- [ ] 确认服务器SSH访问正常
  ```bash
  ssh user@101.37.24.171
  ```
- [ ] 确认项目目录存在
  ```bash
  ls -la /opt/petition-system
  ```
- [ ] 确认部署脚本存在
  ```bash
  ls -la /opt/petition-system/deploy-server.sh
  ```

## 服务器部署 ⏳

### 执行部署
- [ ] SSH登录服务器
- [ ] 进入项目目录
  ```bash
  cd /opt/petition-system
  ```
- [ ] 运行部署脚本
  ```bash
  sudo bash deploy-server.sh
  ```
- [ ] 等待部署完成（约5-10分钟）

### 部署脚本会自动执行
- [ ] 拉取最新代码（git pull）
- [ ] 安装Python依赖
- [ ] 重启后端服务
- [ ] 安装Node.js依赖
- [ ] **构建前端（npm run build）** ← 关键步骤
- [ ] 配置Nginx
- [ ] 重启Nginx

## 部署后验证 ⏳

### 1. 服务状态检查
- [ ] 后端服务运行正常
  ```bash
  sudo systemctl status petition-backend
  # 应显示: active (running)
  ```
- [ ] Nginx服务运行正常
  ```bash
  sudo systemctl status nginx
  # 应显示: active (running)
  ```

### 2. 端点测试
- [ ] 健康检查端点
  ```bash
  curl http://101.37.24.171:8000/api/v1/onlyoffice/health
  # 应返回: {"status":"ok",...}
  ```
- [ ] 下载端点测试
  ```bash
  curl -I http://101.37.24.171:8000/api/v1/onlyoffice/download/file/5
  # 应返回: HTTP/1.1 200 OK
  ```

### 3. 后端日志检查
- [ ] 查看后端日志
  ```bash
  sudo journalctl -u petition-backend -n 50
  ```
- [ ] 确认看到ONLYOFFICE初始化日志
  ```
  [OnlyOfficeService] Initialized with:
    - server_url: http://101.37.24.171:9090
    - backend_public_url: http://101.37.24.171:8000
  ```

### 4. 前端功能测试
- [ ] 访问系统首页
  ```
  http://101.37.24.171
  ```
- [ ] 登录系统
- [ ] 进入文件管理页面
- [ ] 上传测试文件（如果需要）
- [ ] 点击文件预览按钮
- [ ] **验证关键点**：
  - [ ] 不再显示 "Editor config: undefined"
  - [ ] 编辑器正常加载
  - [ ] 文档内容正常显示
  - [ ] 可以正常查看文档

### 5. 浏览器控制台检查
- [ ] 打开浏览器开发者工具（F12）
- [ ] 查看Console标签
- [ ] 应该看到：
  ```javascript
  [OnlyOffice] Editor config: {document: {...}, documentType: "word", ...}
  [OnlyOffice] Editor initialized
  [OnlyOffice] Document ready
  ```
- [ ] 不应该看到：
  ```javascript
  [OnlyOffice] Editor config: undefined  // ✗ 这个错误应该消失
  TypeError: Cannot set properties of undefined
  ```

### 6. 网络请求检查
- [ ] 打开Network标签
- [ ] 点击预览按钮
- [ ] 检查关键请求：
  - [ ] `/api/v1/onlyoffice/config` - 应返回200
  - [ ] `/api/v1/onlyoffice/download/file/{id}` - 应返回200
  - [ ] ONLYOFFICE API脚本加载成功

## 问题排查 ⏳

### 如果编辑器还是不显示

#### 检查1: 前端是否重新构建
```bash
# 在服务器上
cd /opt/petition-system/frontend
ls -la dist/
# 检查dist目录的修改时间是否是最新的
```

#### 检查2: 浏览器缓存
- [ ] 清除浏览器缓存（Ctrl+Shift+Delete）
- [ ] 或使用隐私模式访问

#### 检查3: 后端日志
```bash
sudo journalctl -u petition-backend -f
```
- [ ] 是否有ONLYOFFICE的下载请求？
- [ ] 是否有错误信息？

#### 检查4: Nginx配置
```bash
sudo nginx -t
sudo systemctl restart nginx
```

#### 检查5: 防火墙
```bash
# 确认8000端口对ONLYOFFICE服务器开放
sudo ufw status
```

## 成功标准 ✅

部署成功的标志：
- ✅ 后端服务运行正常
- ✅ 前端构建成功
- ✅ 下载端点返回200
- ✅ 浏览器控制台显示正确的配置对象
- ✅ ONLYOFFICE编辑器正常加载
- ✅ 文档内容正常显示
- ✅ 支持中文文件名
- ✅ 无JavaScript错误

## 回滚方案

如果部署失败，可以回滚：
```bash
cd /opt/petition-system
git log --oneline -5  # 查看最近的提交
git reset --hard HEAD~1  # 回滚到上一个版本
sudo bash deploy-server.sh  # 重新部署
```

## 文档参考

- 详细修复说明：`docs/troubleshooting/ONLYOFFICE编辑器加载问题修复.md`
- 快速部署指南：`快速修复部署.md`
- 完整部署指南：`ONLYOFFICE修复部署指南.md`
- 服务器部署脚本：`deploy-server.sh`

## 联系支持

如果遇到问题，请提供：
1. 浏览器控制台完整错误信息（截图）
2. 后端日志（最近100行）
3. 网络请求详情（Network标签截图）
4. 部署脚本输出

---

**检查清单版本**: v1.0  
**创建日期**: 2026-01-03  
**最后更新**: 2026-01-03 23:20
