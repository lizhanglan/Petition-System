# ONLYOFFICE部署检查清单

**服务器**: 101.37.24.171  
**部署日期**: ___________  
**部署人员**: ___________  

---

## 📋 部署前准备

### 环境检查
- [ ] 服务器可SSH访问
- [ ] 服务器有足够磁盘空间（至少10GB）
- [ ] 服务器有足够内存（至少4GB）
- [ ] Python 3.9+ 已安装
- [ ] Node.js 16+ 已安装
- [ ] PostgreSQL 已安装
- [ ] Nginx 已安装
- [ ] Git 已安装

### 端口检查
- [ ] 80端口可用（HTTP）
- [ ] 8000端口可用（后端API）
- [ ] 9090端口可用（ONLYOFFICE）
- [ ] 5432端口可用（PostgreSQL）

### 外部服务检查
- [ ] MinIO可访问（124.70.74.202:9000）
- [ ] Redis可访问（124.70.74.202:6379）
- [ ] ONLYOFFICE可访问（101.37.24.171:9090）
- [ ] DeepSeek API可用

---

## 🚀 部署步骤

### 1. 代码部署
- [ ] 代码已推送到GitHub
- [ ] 在服务器上克隆代码到 `/opt/petition-system`
- [ ] 代码版本正确

### 2. 后端配置
- [ ] Python虚拟环境已创建
- [ ] Python依赖已安装
- [ ] `.env`文件已配置
- [ ] 数据库已创建
- [ ] 数据库已初始化
- [ ] 标准模板已导入

### 3. 后端环境变量配置

检查 `backend/.env` 文件：

```env
# 关键配置检查
✓ ONLYOFFICE_ENABLED=true
✓ ONLYOFFICE_SERVER_URL=http://101.37.24.171:9090
✓ BACKEND_PUBLIC_URL=http://101.37.24.171:8000
✓ ONLYOFFICE_CALLBACK_URL=http://101.37.24.171:8000/api/v1/onlyoffice/callback
✓ BACKEND_HOST=0.0.0.0
✓ BACKEND_PORT=8000
✓ BACKEND_RELOAD=false
```

- [ ] ONLYOFFICE_ENABLED=true
- [ ] BACKEND_PUBLIC_URL正确
- [ ] ONLYOFFICE_CALLBACK_URL正确
- [ ] 数据库配置正确
- [ ] Redis配置正确
- [ ] MinIO配置正确
- [ ] DeepSeek API配置正确

### 4. 后端服务
- [ ] systemd服务文件已创建
- [ ] 后端服务已启动
- [ ] 后端服务运行正常
- [ ] 后端服务已设置开机自启
- [ ] 后端日志无错误

### 5. 前端配置
- [ ] Node.js依赖已安装
- [ ] 前端已构建（npm run build）
- [ ] dist目录已生成
- [ ] 静态文件完整

### 6. Nginx配置
- [ ] Nginx配置文件已创建
- [ ] Nginx配置已启用
- [ ] Nginx配置测试通过
- [ ] Nginx已重启
- [ ] Nginx已设置开机自启

### 7. 防火墙配置
- [ ] 80端口已开放
- [ ] 8000端口已开放
- [ ] 9090端口已开放
- [ ] 防火墙规则已保存

---

## ✅ 功能验证

### 基础功能
- [ ] 前端页面可访问（http://101.37.24.171）
- [ ] 可以注册用户
- [ ] 可以登录系统
- [ ] 可以上传文件
- [ ] 可以查看文件列表

### 后端API
- [ ] API可访问（http://101.37.24.171:8000）
- [ ] 健康检查通过（/api/v1/auth/me）
- [ ] 数据库连接正常
- [ ] Redis连接正常
- [ ] MinIO连接正常

### ONLYOFFICE服务
- [ ] ONLYOFFICE可访问（http://101.37.24.171:9090）
- [ ] 健康检查通过（/healthcheck）
- [ ] API脚本可加载（/web-apps/apps/api/documents/api.js）

### ONLYOFFICE集成
- [ ] 配置API正常（/api/v1/onlyoffice/config）
- [ ] 下载代理正常（/api/v1/onlyoffice/download/file/{id}）
- [ ] 回调端点可访问（/api/v1/onlyoffice/callback）

### 文件预览功能
- [ ] 上传DOCX文件
- [ ] 点击"预览"按钮
- [ ] ONLYOFFICE编辑器加载
- [ ] 文档内容正常显示
- [ ] 可以滚动查看文档

### 文书生成功能
- [ ] 选择模板
- [ ] 输入需求
- [ ] AI生成文书
- [ ] 右侧显示ONLYOFFICE预览
- [ ] 文书内容正常显示

### 文书管理功能
- [ ] 查看文书列表
- [ ] 点击"查看"按钮
- [ ] ONLYOFFICE预览正常
- [ ] 点击"在线编辑"按钮
- [ ] ONLYOFFICE编辑器打开
- [ ] 可以编辑文档
- [ ] 保存功能正常

### 文件研判功能
- [ ] 点击"研判"按钮
- [ ] 左侧ONLYOFFICE预览正常
- [ ] 点击"开始研判"
- [ ] AI研判正常
- [ ] 右侧显示研判结果

---

## 🔍 连接测试

### 从服务器测试

```bash
# 1. 测试ONLYOFFICE
curl http://101.37.24.171:9090/healthcheck

# 2. 测试后端
curl http://101.37.24.171:8000/api/v1/auth/me

# 3. 测试前端
curl http://101.37.24.171

# 4. 测试ONLYOFFICE到后端的连接
curl http://101.37.24.171:8000/api/v1/onlyoffice/download/file/1
```

测试结果：
- [ ] ONLYOFFICE健康检查通过
- [ ] 后端API可访问
- [ ] 前端页面可访问
- [ ] ONLYOFFICE可以访问后端

### 从浏览器测试

1. 打开浏览器开发者工具（F12）
2. 访问 http://101.37.24.171
3. 登录系统
4. 上传文件并预览
5. 查看Network标签

检查以下请求：
- [ ] GET /api/v1/files/{id}/preview - 200 OK
- [ ] POST /api/v1/onlyoffice/config - 200 OK
- [ ] GET http://101.37.24.171:9090/web-apps/apps/api/documents/api.js - 200 OK

---

## 📊 性能测试

### 响应时间
- [ ] 首页加载 < 2秒
- [ ] 文件列表加载 < 1秒
- [ ] 文件预览加载 < 3秒
- [ ] ONLYOFFICE编辑器加载 < 5秒
- [ ] AI生成文书 < 30秒

### 并发测试
- [ ] 5个用户同时预览文件
- [ ] 3个用户同时编辑文档
- [ ] 系统响应正常
- [ ] 无明显卡顿

---

## 🐛 问题排查

### 如果ONLYOFFICE无法加载

检查项：
- [ ] 后端日志：`sudo journalctl -u petition-backend -f`
- [ ] Nginx日志：`sudo tail -f /var/log/nginx/error.log`
- [ ] 浏览器控制台：F12 → Console
- [ ] Network标签：查看失败的请求

常见问题：
- [ ] 后端URL配置错误
- [ ] ONLYOFFICE无法访问后端
- [ ] 防火墙阻止
- [ ] 文件URL不可访问

### 如果文档无法显示

检查项：
- [ ] 测试下载代理：`curl http://101.37.24.171:8000/api/v1/onlyoffice/download/file/1`
- [ ] 检查MinIO连接
- [ ] 检查文件是否存在
- [ ] 查看后端日志

---

## 📝 部署记录

### 部署信息
- 部署日期：___________
- 部署人员：___________
- 代码版本：___________
- 部署时长：___________

### 配置信息
- 服务器IP：101.37.24.171
- 后端端口：8000
- ONLYOFFICE端口：9090
- 数据库：PostgreSQL
- 对象存储：MinIO (124.70.74.202:9000)
- 缓存：Redis (124.70.74.202:6379)

### 服务状态
- 后端服务：[ ] 运行中 [ ] 已停止
- Nginx服务：[ ] 运行中 [ ] 已停止
- ONLYOFFICE：[ ] 运行中 [ ] 已停止
- PostgreSQL：[ ] 运行中 [ ] 已停止

### 遇到的问题
```
[记录部署过程中遇到的问题和解决方案]




```

### 备注
```
[其他需要记录的信息]




```

---

## ✅ 最终确认

- [ ] 所有功能测试通过
- [ ] 性能测试通过
- [ ] 无明显错误和警告
- [ ] 文档已更新
- [ ] 部署记录已完成

---

## 📞 联系方式

如有问题，请联系：
- 技术支持：___________
- 项目负责人：___________

---

**检查人员签名**: ___________  
**检查日期**: ___________  
**检查结果**: [ ] 通过 [ ] 不通过  

---

**创建时间**: 2026-01-03 23:00  
**文档版本**: 1.0
