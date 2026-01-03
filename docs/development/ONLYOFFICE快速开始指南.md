# ONLYOFFICE集成快速开始指南

## 概述

本指南帮助开发人员快速开始ONLYOFFICE集成工作，包含最小可行实现（MVP）。

## 前置条件

- ONLYOFFICE服务器：`http://101.37.24.171:9090`
- Python 3.9+
- Node.js 16+
- 已有的MinIO存储服务

## 第一步：验证ONLYOFFICE服务

### 1.1 健康检查

```bash
curl http://101.37.24.171:9090/healthcheck
# 预期返回：true
```

### 1.2 测试API可用性

```bash
curl http://101.37.24.171:9090/web-apps/apps/api/documents/api.js
# 预期返回：JavaScript代码
```

### 1.3 检查版本信息

访问：`http://101.37.24.171:9090/welcome/`

## 第二步：配置环境变量

**注意**：你的ONLYOFFICE服务器已关闭JWT验证，无需配置JWT密钥，简化了集成流程！

### 2.1 更新 `.env` 文件

```bash
# ONLYOFFICE配置（无JWT版本）
ONLYOFFICE_ENABLED=true
ONLYOFFICE_SERVER_URL=http://101.37.24.171:9090
ONLYOFFICE_JWT_ENABLED=false
ONLYOFFICE_CALLBACK_URL=http://你的后端地址/api/v1/onlyoffice/callback
```

### 2.2 更新 `.env.example`

同样添加上述配置。

## 第三步：最小实现（MVP）

**注意**：由于JWT已关闭，实现更简单，预计节省1-2天开发时间！

### 3.1 创建配置类（5分钟）

**文件**：`backend/app/core/config.py`

```python
# 在Settings类中添加
class Settings(BaseSettings):
    # ... 现有配置 ...
    
    # ONLYOFFICE配置（无JWT版本）
    ONLYOFFICE_ENABLED: bool = True
    ONLYOFFICE_SERVER_URL: str = "http://101.37.24.171:9090"
    ONLYOFFICE_JWT_ENABLED: bool = False
    ONLYOFFICE_CALLBACK_URL: str = ""
```

### 3.2 创建服务类（20分钟，简化版）

**文件**：`backend/app/services/onlyoffice_service.py`

```python
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
from app.core.config import settings

class OnlyOfficeService:
    """ONLYOFFICE文档服务（无JWT版本）"""
    
    def __init__(self):
        self.server_url = settings.ONLYOFFICE_SERVER_URL
        self.callback_url = settings.ONLYOFFICE_CALLBACK_URL
    
    def generate_document_key(self, file_id: int, updated_at: datetime) -> str:
        """生成文档唯一key（用于缓存和版本控制）"""
        key_string = f"{file_id}_{updated_at.timestamp()}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get_document_type(self, file_extension: str) -> str:
        """根据文件扩展名获取文档类型"""
        ext = file_extension.lower().lstrip('.')
        
        word_exts = ['doc', 'docx', 'docm', 'dot', 'dotx', 'dotm', 'odt', 'fodt', 'ott', 'rtf', 'txt', 'html', 'htm', 'mht', 'pdf', 'djvu', 'fb2', 'epub', 'xps']
        cell_exts = ['xls', 'xlsx', 'xlsm', 'xlt', 'xltx', 'xltm', 'ods', 'fods', 'ots', 'csv']
        slide_exts = ['pps', 'ppsx', 'ppsm', 'ppt', 'pptx', 'pptm', 'pot', 'potx', 'potm', 'odp', 'fodp', 'otp']
        
        if ext in word_exts:
            return 'word'
        elif ext in cell_exts:
            return 'cell'
        elif ext in slide_exts:
            return 'slide'
        else:
            return 'word'  # 默认
    
    async def get_editor_config(
        self,
        file_id: int,
        file_url: str,
        file_name: str,
        file_type: str,
        user_id: str,
        user_name: str,
        mode: str = 'view',
        updated_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        生成ONLYOFFICE编辑器配置
        
        Args:
            file_id: 文件ID
            file_url: 文件下载URL（供ONLYOFFICE访问）
            file_name: 文件名
            file_type: 文件类型（扩展名）
            user_id: 用户ID
            user_name: 用户名
            mode: 模式 ('view' 或 'edit')
            updated_at: 文件更新时间
        
        Returns:
            编辑器配置字典
        """
        if updated_at is None:
            updated_at = datetime.now()
        
        # 生成文档key
        document_key = self.generate_document_key(file_id, updated_at)
        
        # 获取文档类型
        document_type = self.get_document_type(file_type)
        
        # 配置（无JWT版本，更简单）
        config = {
            "document": {
                "fileType": file_type.lower().lstrip('.'),
                "key": document_key,
                "title": file_name,
                "url": file_url,
                "permissions": {
                    "edit": mode == 'edit',
                    "download": True,
                    "print": True,
                    "review": mode == 'edit',
                    "comment": mode == 'edit'
                }
            },
            "documentType": document_type,
            "editorConfig": {
                "mode": mode,
                "lang": "zh-CN",
                "callbackUrl": f"{self.callback_url}?fileId={file_id}",
                "user": {
                    "id": str(user_id),
                    "name": user_name
                },
                "customization": {
                    "autosave": True,
                    "forcesave": True,
                    "comments": mode == 'edit',
                    "chat": False,
                    "compactHeader": False,
                    "feedback": False,
                    "help": False,
                    "hideRightMenu": False,
                    "plugins": True,
                    "toolbarNoTabs": False,
                    "uiTheme": "theme-light"
                }
            }
        }
        
        return config
    
    async def handle_callback(
        self,
        callback_data: Dict[str, Any],
        file_id: int
    ) -> Dict[str, Any]:
        """
        处理ONLYOFFICE保存回调
        
        回调状态：
        0 - 文档未找到
        1 - 文档正在编辑
        2 - 文档准备保存
        3 - 文档保存错误
        4 - 文档关闭无变化
        6 - 文档正在编辑，但保存当前状态
        7 - 强制保存错误
        
        Args:
            callback_data: 回调数据
            file_id: 文件ID
        
        Returns:
            响应数据
        """
        status = callback_data.get('status')
        
        print(f"[OnlyOffice] Callback received for file {file_id}, status: {status}")
        
        # 状态2或6表示需要保存
        if status in [2, 6]:
            download_url = callback_data.get('url')
            if not download_url:
                return {"error": 1, "message": "Download URL not provided"}
            
            print(f"[OnlyOffice] Document ready to save, download URL: {download_url}")
            
            # 这里返回成功，实际保存逻辑在API端点中处理
            return {
                "error": 0,
                "message": "Document saved successfully",
                "download_url": download_url
            }
        
        # 其他状态直接返回成功
        return {"error": 0}

# 创建全局实例
onlyoffice_service = OnlyOfficeService()
```

### 3.3 创建API端点（30分钟）

**文件**：`backend/app/api/v1/endpoints/onlyoffice.py`

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.user import User
from app.models.file import File
from app.models.document import Document
from app.api.v1.endpoints.auth import get_current_user
from app.services.onlyoffice_service import onlyoffice_service
from app.core.minio_client import minio_client

router = APIRouter()

class EditorConfigRequest(BaseModel):
    file_id: int
    mode: str = 'view'  # 'view' or 'edit'

@router.post("/config")
async def get_editor_config(
    request: EditorConfigRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取ONLYOFFICE编辑器配置"""
    
    # 查询文件
    result = await db.execute(
        select(File).where(
            File.id == request.file_id,
            File.user_id == current_user.id
        )
    )
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 生成文件访问URL（供ONLYOFFICE下载）
    file_url = minio_client.get_file_url(file.storage_path, expires=3600, inline=True)
    
    # 生成编辑器配置
    config = await onlyoffice_service.get_editor_config(
        file_id=file.id,
        file_url=file_url,
        file_name=file.file_name,
        file_type=file.file_type,
        user_id=str(current_user.id),
        user_name=current_user.full_name or current_user.username,
        mode=request.mode,
        updated_at=file.updated_at
    )
    
    return config

@router.post("/callback")
async def handle_callback(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """处理ONLYOFFICE保存回调"""
    
    # 获取回调数据
    callback_data = await request.json()
    
    # 从查询参数获取file_id
    file_id = request.query_params.get('fileId')
    if not file_id:
        return {"error": 1, "message": "File ID not provided"}
    
    file_id = int(file_id)
    
    # 处理回调
    result = await onlyoffice_service.handle_callback(callback_data, file_id)
    
    # 如果需要保存文件
    if result.get('download_url'):
        download_url = result['download_url']
        
        # 从ONLYOFFICE下载编辑后的文件
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(download_url)
            if response.status_code == 200:
                file_bytes = response.content
                
                # 查询文件记录
                db_result = await db.execute(
                    select(File).where(File.id == file_id)
                )
                file = db_result.scalar_one_or_none()
                
                if file:
                    # 上传到MinIO（覆盖原文件）
                    await minio_client.upload_file(
                        file.storage_path,
                        file_bytes,
                        file.content_type
                    )
                    
                    # 更新文件记录
                    file.file_size = len(file_bytes)
                    await db.commit()
                    
                    print(f"[OnlyOffice] File {file_id} saved successfully")
    
    return result

@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "onlyoffice_enabled": onlyoffice_service.jwt_enabled,
        "server_url": onlyoffice_service.server_url
    }
```

### 3.4 注册路由（2分钟）

**文件**：`backend/app/api/v1/__init__.py`

```python
from app.api.v1.endpoints import onlyoffice

# 在api_router中添加
api_router.include_router(
    onlyoffice.router,
    prefix="/onlyoffice",
    tags=["onlyoffice"]
)
```

### 3.5 创建前端组件（1小时）

**文件**：`frontend/src/components/OnlyOfficeEditor.vue`

```vue
<template>
  <div class="onlyoffice-editor">
    <div v-if="loading" class="loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>正在加载编辑器...</span>
    </div>
    <div v-else-if="error" class="error">
      <el-alert :title="error" type="error" show-icon />
    </div>
    <div v-else id="onlyoffice-editor" :style="{ height: height }"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

interface Props {
  fileId: number
  mode?: 'view' | 'edit'
  height?: string
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'view',
  height: '600px'
})

const emit = defineEmits<{
  save: []
  close: []
  error: [error: string]
}>()

const loading = ref(true)
const error = ref('')
let editor: any = null

// 加载ONLYOFFICE API脚本
const loadOnlyOfficeScript = (): Promise<void> => {
  return new Promise((resolve, reject) => {
    // 检查是否已加载
    if (window.DocsAPI) {
      resolve()
      return
    }
    
    const script = document.createElement('script')
    script.src = 'http://101.37.24.171:9090/web-apps/apps/api/documents/api.js'
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Failed to load ONLYOFFICE API'))
    document.head.appendChild(script)
  })
}

// 初始化编辑器
const initEditor = async () => {
  try {
    loading.value = true
    error.value = ''
    
    // 加载API脚本
    await loadOnlyOfficeScript()
    
    // 获取编辑器配置
    const response = await fetch('/api/v1/onlyoffice/config', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        file_id: props.fileId,
        mode: props.mode
      })
    })
    
    if (!response.ok) {
      throw new Error('Failed to get editor config')
    }
    
    const config = await response.json()
    
    // 添加事件处理
    config.events = {
      onDocumentReady: () => {
        console.log('[OnlyOffice] Document ready')
        loading.value = false
      },
      onError: (event: any) => {
        console.error('[OnlyOffice] Error:', event)
        error.value = `编辑器错误: ${event.data}`
        emit('error', error.value)
      },
      onWarning: (event: any) => {
        console.warn('[OnlyOffice] Warning:', event)
      }
    }
    
    // 初始化编辑器
    editor = new window.DocsAPI.DocEditor('onlyoffice-editor', config)
    
  } catch (err: any) {
    console.error('[OnlyOffice] Init error:', err)
    error.value = err.message || '编辑器初始化失败'
    loading.value = false
    emit('error', error.value)
  }
}

// 销毁编辑器
const destroyEditor = () => {
  if (editor) {
    try {
      editor.destroyEditor()
    } catch (err) {
      console.error('[OnlyOffice] Destroy error:', err)
    }
    editor = null
  }
}

onMounted(() => {
  initEditor()
})

onUnmounted(() => {
  destroyEditor()
})
</script>

<style scoped>
.onlyoffice-editor {
  width: 100%;
  height: 100%;
  position: relative;
}

.loading,
.error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 10px;
}

#onlyoffice-editor {
  width: 100%;
}
</style>
```

## 第四步：测试验证（10分钟）

1. 启动后端服务
2. 启动前端服务
3. 上传一个DOCX文件
4. 点击预览，应该看到ONLYOFFICE编辑器
5. 切换到编辑模式，尝试编辑并保存

## 第五步：验证清单

- [x] ONLYOFFICE服务可访问（已验证✅）
- [x] ONLYOFFICE版本：9.2.1（已确认✅）
- [x] JWT验证已关闭（已确认✅）
- [ ] 后端API端点正常
- [ ] 前端组件加载成功
- [ ] 文档可以预览
- [ ] 文档可以编辑
- [ ] 编辑后可以保存

## 常见问题

### Q1: 编辑器显示"下载错误"

**原因**：ONLYOFFICE无法访问文件URL

**解决**：
- 确保MinIO的URL可以从ONLYOFFICE服务器访问
- 检查防火墙规则
- 使用公网IP而不是localhost

### Q2: 保存回调失败

**原因**：回调URL不可访问

**解决**：
- 确保 `ONLYOFFICE_CALLBACK_URL` 配置正确
- 使用公网可访问的URL
- 检查防火墙规则

### Q4: 编辑器加载很慢

**原因**：网络延迟或文件太大

**解决**：
- 使用CDN加速ONLYOFFICE静态资源
- 优化文件大小
- 增加超时时间

## 下一步

完成MVP后，可以继续：

1. 添加版本管理集成
2. 实现协作编辑
3. 优化性能
4. 添加更多自定义功能
5. 移除旧的预览服务

## 参考资源

- [ONLYOFFICE API文档](https://api.onlyoffice.com/editors/basic)
- [ONLYOFFICE配置示例](https://api.onlyoffice.com/editors/config/)
- [JWT官方文档](https://jwt.io/)

## 支持

如有问题，请查看：
- `docs/development/ONLYOFFICE重构方案.md` - 完整方案
- `docs/development/ONLYOFFICE重构任务清单.md` - 详细任务
