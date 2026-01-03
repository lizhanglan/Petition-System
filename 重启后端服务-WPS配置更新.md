# 重启后端服务 - WPS配置更新

## 问题
已在 `backend/.env` 中添加了WPS配置，但服务还在使用旧配置。

## 解决方案

### 方法1: 使用start.bat重启（推荐）
```bash
# 1. 停止当前运行的后端服务（按Ctrl+C）
# 2. 重新运行
start.bat
```

### 方法2: 手动重启
```bash
# 1. 找到Python进程并停止
# 在任务管理器中结束 python.exe 进程（PID: 45104）

# 2. 重新启动后端
cd backend
python run.py
```

### 方法3: 使用PowerShell重启
```powershell
# 停止后端进程
Stop-Process -Id 45104 -Force

# 等待几秒
Start-Sleep -Seconds 2

# 重新启动
cd backend
python run.py
```

## 验证配置

重启后，查看日志应该显示：
```
[PreviewSelector] 尝试使用WPS服务...
[WPS] Requesting preview URL for: ...
```

而不是：
```
[PreviewSelector] WPS服务未启用（WPS_ENABLED=False）
```

## 已更新的配置

`backend/.env` 文件已添加：
```bash
# WPS开放平台配置
WPS_APP_ID=SX20260103SMMPSL
WPS_APP_SECRET=lzmInGanZmLBIqbyrAoSyzKRYOANYksZ
WPS_API_BASE=https://open.wps.cn
WPS_ENABLED=true
```
