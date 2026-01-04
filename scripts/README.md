# 脚本目录说明

**整理日期**: 2026-01-04

---

## 目录结构

```
scripts/
├── README.md              # 本文档
├── deployment/            # 部署脚本（生产环境）
├── debug/                 # 调试脚本（问题排查）
└── archive/               # 归档脚本（已过期或不常用）
```

---

## 根目录核心脚本

### 统一启动脚本（推荐）

#### Windows
- **run.bat** - 统一启动脚本（交互式菜单）
  - 用途：本地开发和Docker部署的统一入口
  - 使用：双击运行或 `run.bat`
  - 功能：完整的项目管理功能

#### Linux/Mac
- **run.sh** - 统一启动脚本（交互式菜单 + 命令行）
  - 用途：本地开发和Docker部署的统一入口
  - 使用：`./run.sh` 或 `./run.sh [command]`
  - 功能：完整的项目管理功能

详见：**[统一启动脚本说明.md](./统一启动脚本说明.md)**

---

## deployment/ - 部署脚本

### 云服务器部署
- **deploy-cloud.sh** - 云服务器部署脚本
  - 用途：在云服务器上部署项目
  - 使用：`./scripts/deployment/deploy-cloud.sh`

- **deploy-server.sh** - 服务器部署脚本
  - 用途：服务器端部署流程
  - 使用：`./scripts/deployment/deploy-server.sh`

---

## debug/ - 调试脚本

### 代码检查
- **check-server-code.bat** - 检查服务器代码是否已更新（Windows）
  - 用途：对比宿主机和容器内的代码版本
  - 使用：`scripts\debug\check-server-code.bat`

- **check-server-code.sh** - 检查服务器代码是否已更新（Linux）
  - 用途：对比宿主机和容器内的代码版本
  - 使用：`./scripts/debug/check-server-code.sh`

### 容器检查
- **check-hot-reload-status.bat** - 检查容器热更新支持状态
  - 用途：检查Docker容器是否支持代码热更新
  - 使用：`scripts\debug\check-hot-reload-status.bat`

- **server-commands.sh** - 服务器命令序列
  - 用途：在服务器上执行一系列调试命令
  - 使用：`./scripts/debug/server-commands.sh`

---

## archive/ - 归档脚本

以下脚本已过期或不常用，保留作为历史参考：

- **deploy-with-mount.bat** - 部署带代码挂载的配置（已过期）
- **push-and-rebuild.bat** - 推送代码并触发服务器重建（已过期）
- **restart-backend.bat** - 重启后端服务（本地开发用，已不推荐）
- **rebuild-frontend.sh** - 重建前端容器（已整合到部署脚本）

---

## 使用指南

### 本地开发

#### Windows
```bash
# 启动开发环境
start.bat

# 部署到本地Docker
deploy.bat
```

#### Linux/Mac
```bash
# 部署到本地Docker
./deploy.sh
```

### 云服务器部署

```bash
# 部署到云服务器
./scripts/deployment/deploy-cloud.sh

# 或使用服务器部署脚本
./scripts/deployment/deploy-server.sh
```

### 问题排查

#### 检查服务器代码版本
```bash
# Windows
scripts\debug\check-server-code.bat

# Linux
./scripts/debug/check-server-code.sh
```

#### 检查容器热更新状态
```bash
scripts\debug\check-hot-reload-status.bat
```

---

## 脚本维护

### 添加新脚本
1. 根据用途放入对应目录：
   - `deployment/` - 生产部署相关
   - `debug/` - 调试和问题排查
   - `archive/` - 过期或不常用

2. 更新本README文档

3. 确保脚本有执行权限（Linux/Mac）：
   ```bash
   chmod +x scripts/deployment/your-script.sh
   ```

### 归档旧脚本
1. 将不再使用的脚本移到 `archive/`
2. 在本文档中标注为"已过期"
3. 说明替代方案

---

## 常见问题

### Q: 为什么要整理脚本？
A: 根目录有太多临时调试脚本，影响项目结构清晰度。整理后更易于维护和查找。

### Q: 归档的脚本还能用吗？
A: 可以，但不推荐。它们可能依赖旧的配置或已有更好的替代方案。

### Q: 如何选择使用哪个部署脚本？
A: 
- 本地开发：使用根目录的 `start.bat` 或 `deploy.sh`
- 云服务器：使用 `scripts/deployment/deploy-cloud.sh`
- 问题排查：使用 `scripts/debug/` 下的相应脚本

---

**维护者**: Kiro AI Assistant  
**最后更新**: 2026-01-04  
**版本**: 1.0
