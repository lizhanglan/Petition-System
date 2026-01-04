# ONLYOFFICE JWT验证错误修复

## 问题描述

ONLYOFFICE编辑器返回JWT验证错误：
```
errorCode: -20
errorDescription: '文档安全令牌的格式不正确'
```

## 根本原因

- ONLYOFFICE服务器启用了JWT验证（`token.enable.browser: true`）
- 后端配置生成的编辑器配置中没有包含JWT令牌
- 用户明确表示不需要JWT验证

## 解决方案

### 方案1：禁用JWT验证（推荐）

在服务器上运行脚本禁用JWT：

```bash
# Linux/Mac
bash disable-onlyoffice-jwt.sh

# Windows（本地）
disable-onlyoffice-jwt.bat
```

### 方案2：手动禁用JWT

```bash
# 1. 创建配置文件
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

# 2. 重启容器
docker restart gracious_curran

# 3. 等待10秒让容器完全启动
sleep 10
```

### 方案3：实现JWT令牌生成（复杂，不推荐）

如果将来需要JWT验证，需要：

1. 安装PyJWT库：
```bash
pip install PyJWT
```

2. 在 `backend/app/services/onlyoffice_service.py` 中添加JWT生成：
```python
import jwt
from datetime import datetime, timedelta

def generate_jwt_token(self, config: dict) -> str:
    """生成JWT令牌"""
    secret = "ZODquk6vSezRhih5AJkrrlyYsvMIvVgj"
    
    payload = {
        "document": config["document"],
        "documentType": config["documentType"],
        "editorConfig": config["editorConfig"],
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    
    return jwt.encode(payload, secret, algorithm="HS256")

# 在配置中添加token
config["token"] = self.generate_jwt_token(config)
```

## 验证修复

1. 清除浏览器缓存（Ctrl+Shift+Delete）
2. 刷新页面（Ctrl+F5）
3. 打开文件预览
4. 检查浏览器控制台，应该看到：
   - `✅ App ready`
   - `✅ Document ready`
   - 没有JWT错误

## 相关文件

- `disable-onlyoffice-jwt.sh` - Linux/Mac禁用脚本
- `disable-onlyoffice-jwt.bat` - Windows禁用脚本
- `backend/app/services/onlyoffice_service.py` - ONLYOFFICE服务配置
- ONLYOFFICE配置文件：`/etc/onlyoffice/documentserver/local.json`（容器内）

## 技术细节

### JWT验证流程

1. 前端请求编辑器配置
2. 后端生成配置（包含文档URL、权限等）
3. 如果启用JWT，后端需要用secret签名整个配置
4. ONLYOFFICE服务器验证JWT签名
5. 验证通过后加载文档

### 为什么禁用JWT

- 简化配置和维护
- 用户明确表示不需要
- 系统已有其他安全措施（用户认证、文件权限等）
- ONLYOFFICE通过Docker内部网络访问，不暴露在公网

## 修复时间线

1. ✅ 发现JWT验证错误（errorCode: -20）
2. ✅ 确认ONLYOFFICE配置启用了JWT
3. ✅ 用户确认不需要JWT验证
4. ✅ 创建禁用脚本
5. ⏳ 等待在服务器上执行脚本
6. ⏳ 验证修复效果
