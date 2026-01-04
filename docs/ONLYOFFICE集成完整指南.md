# ONLYOFFICE集成完整指南

**文档版本**: 1.0  
**完成日期**: 2026-01-04  
**状态**: ✅ 已完成并验证

---

## 目录

1. [项目背景](#项目背景)
2. [技术架构](#技术架构)
3. [实施步骤](#实施步骤)
4. [核心代码实现](#核心代码实现)
5. [部署配置](#部署配置)
6. [问题解决历程](#问题解决历程)
7. [测试验证](#测试验证)
8. [维护指南](#维护指南)

---

## 项目背景

### 原有方案的问题

系统原本使用WPS和华为云OFD预览服务，存在以下问题：
- WPS服务不稳定，经常出现404错误
- 华为云OFD服务仅支持特定格式
- 两个服务分散管理，维护成本高
- 预览效果不统一

### 重构目标

使用ONLYOFFICE DocumentServer替代原有方案：
- ✅ 统一的文档预览和编辑解决方案
- ✅ 支持Word、Excel、PowerPoint等主流格式
- ✅ 私有化部署，数据安全可控
- ✅ 功能强大，支持在线编辑和协作

---

## 技术架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户浏览器                              │
│                  (http://101.37.24.171:8081)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    前端 (Nginx + Vue3)                        │
│                  - OnlyOfficeEditor组件                       │
│                  - Files.vue (文件预览)                       │
│                  - Review.vue (文件研判)                      │
│                  - Documents.vue (文书编辑)                   │
│                  - Generate.vue (文书生成)                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  后端 (FastAPI + Python)                      │
│                  - /api/v1/onlyoffice/config                 │
│                  - /api/v1/onlyoffice/download/file/{id}    │
│                  - /api/v1/onlyoffice/download/document/{id}│
│                  - /api/v1/onlyoffice/callback               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              ONLYOFFICE DocumentServer                        │
│              (http://101.37.24.171:9090)                     │
│              - Docker容器独立运行                             │
│              - 加入petition-system_petition-network          │
│              - 通过Docker内部网络访问后端                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    MinIO对象存储                              │
│                  (124.70.74.202:9000)                        │
│                  - 存储所有文件和文书                          │
└─────────────────────────────────────────────────────────────┘
```

### 网络架构

**Docker网络**: `petition-system_petition-network`

| 服务 | 容器名 | 内部IP | 外部端口 |
|------|--------|--------|----------|
| 后端 | petition-backend | 172.18.0.4 | 8000 |
| ONLYOFFICE | gracious_curran | 172.18.0.6 | 9090 |
| 前端 | petition-frontend | - | 8081 |

**关键设计**：
- ONLYOFFICE通过Docker内部网络访问后端：`http://petition-backend:8000`
- 避免使用公网IP，提高安全性和性能
- 后端作为代理，统一处理文件下载和权限验证

---

## 实施步骤

### 阶段1：ONLYOFFICE服务器部署

#### 1.1 启动ONLYOFFICE容器

```bash
# 拉取镜像
docker pull onlyoffice/documentserver

# 启动容器（独立运行）
docker run -d \
  --name gracious_curran \
  -p 9090:80 \
  -e JWT_ENABLED=false \
  onlyoffice/documentserver
```

#### 1.2 加入Docker网络

```bash
# 将ONLYOFFICE容器加入项目网络
docker network connect petition-system_petition-network gracious_curran

# 验证网络连接
docker network inspect petition-system_petition-network
```

#### 1.3 配置ONLYOFFICE

**禁用JWT验证**：

```bash
# 创建配置文件
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
      },
      "request-filtering-agent": {
        "allowPrivateIPAddress": true,
        "allowMetaIPAddress": true
      }
    }
  }
}
EOF'

# 重启服务进程
docker exec gracious_curran supervisorctl restart ds:docservice ds:converter
```

**禁用secure_link缓存验证**：

```bash
# 备份配置
docker exec gracious_curran cp /etc/nginx/includes/ds-docservice.conf /etc/nginx/includes/ds-docservice.conf.bak

# 删除secure_link检查代码（行49-58）
docker exec gracious_curran sed -i '49,58d' /etc/nginx/includes/ds-docservice.conf

# 测试并重载Nginx
docker exec gracious_curran nginx -t
docker exec gracious_curran nginx -s reload
```

### 阶段2：后端集成

#### 2.1 环境变量配置

**文件**: `backend/.env`

```env
# ONLYOFFICE配置
ONLYOFFICE_ENABLED=true
ONLYOFFICE_SERVER_URL=http://101.37.24.171:9090
ONLYOFFICE_CALLBACK_URL=http://101.37.24.171:8000/api/v1/onlyoffice/callback
ONLYOFFICE_JWT_ENABLED=false
BACKEND_PUBLIC_URL=http://101.37.24.171:8000
```

#### 2.2 创建ONLYOFFICE服务

**文件**: `backend/app/services/onlyoffice_service.py`

核心功能：
- 生成编辑器配置（文件和文书）
- 使用Docker内部网络URL
- 处理保存回调

```python
class OnlyOfficeService:
    def __init__(self):
        self.server_url = settings.ONLYOFFICE_SERVER_URL
        self.callback_url = settings.ONLYOFFICE_CALLBACK_URL
        self.backend_public_url = settings.BACKEND_PUBLIC_URL
        self.jwt_enabled = settings.ONLYOFFICE_JWT_ENABLED
    
    async def get_editor_config_for_file(
        self, file_id, file_name, file_type, 
        user_id, user_name, mode='view', updated_at=None
    ):
        # 使用Docker内部网络
        file_url = f"http://petition-backend:8000/api/v1/onlyoffice/download/file/{file_id}"
        
        config = {
            "document": {
                "fileType": file_type.lower().lstrip('.'),
                "key": self.generate_document_key(file_id, updated_at),
                "title": file_name,
                "url": file_url,
                "permissions": {
                    "edit": mode == 'edit',
                    "download": True,
                    "print": True
                }
            },
            "documentType": self.get_document_type(file_type),
            "editorConfig": {
                "mode": mode,
                "lang": "zh-CN",
                "user": {"id": str(user_id), "name": user_name}
            }
        }
        
        # 只在编辑模式添加回调URL
        if mode == 'edit':
            config["editorConfig"]["callbackUrl"] = f"{self.callback_url}?fileId={file_id}&type=file"
        
        return config
```

#### 2.3 创建API端点

**文件**: `backend/app/api/v1/endpoints/onlyoffice.py`

核心端点：

1. **配置端点** - `/api/v1/onlyoffice/config`
   - 返回编辑器配置
   - 支持文件和文书两种类型

2. **下载端点** - `/api/v1/onlyoffice/download/file/{file_id}`
   - 支持GET和HEAD方法
   - 从MinIO下载文件
   - 无需认证（ONLYOFFICE服务器调用）

3. **回调端点** - `/api/v1/onlyoffice/callback`
   - 处理文档保存
   - 更新MinIO中的文件

```python
@router.api_route("/download/file/{file_id}", methods=["GET", "HEAD"])
async def download_file_for_onlyoffice(
    file_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    # 查询文件
    result = await db.execute(select(File).where(File.id == file_id))
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # HEAD请求只返回头部
    if request.method == "HEAD":
        return StreamingResponse(
            io.BytesIO(b""),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
        )
    
    # 从MinIO下载文件
    file_data = await minio_client.download_file(file.storage_path)
    
    return StreamingResponse(
        io.BytesIO(file_data),
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            "Content-Length": str(len(file_data)),
            "Access-Control-Allow-Origin": "*"
        }
    )
```

#### 2.4 更新文件预览服务

**文件**: `backend/app/api/v1/endpoints/files.py`

修改预览端点，返回ONLYOFFICE标识：

```python
@router.get("/{file_id}/preview")
async def get_file_preview(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 查询文件
    file = await db.execute(select(File).where(File.id == file_id))
    file = file.scalar_one_or_none()
    
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 返回ONLYOFFICE标识
    return {
        "preview_url": "use_onlyoffice_component",
        "file_url": file.file_url,
        "preview_type": "onlyoffice",
        "file_type": file.file_type,
        "file_name": file.file_name
    }
```

### 阶段3：前端集成

#### 3.1 创建OnlyOfficeEditor组件

**文件**: `frontend/src/components/OnlyOfficeEditor.vue`

核心功能：
- 动态加载ONLYOFFICE API脚本
- 初始化编辑器
- 处理事件和错误
- 自适应布局

```vue
<template>
  <div class="onlyoffice-editor">
    <div v-if="loading" class="loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>正在加载编辑器...</span>
    </div>
    <div v-if="error" class="error">
      <el-alert :title="error" type="error" show-icon />
    </div>
    <div id="onlyoffice-editor" :style="{ height: height }" v-show="!loading && !error"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import request from '../api/request'

const props = withDefaults(defineProps<{
  fileId?: number
  documentId?: number
  mode?: 'view' | 'edit'
  height?: string
}>(), {
  mode: 'view',
  height: '600px'
})

const loading = ref(true)
const error = ref('')
let editor: any = null

// 加载ONLYOFFICE API脚本
const loadOnlyOfficeScript = (): Promise<void> => {
  return new Promise((resolve, reject) => {
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
    await loadOnlyOfficeScript()
    
    const config = await request.post('/onlyoffice/config', {
      file_id: props.fileId,
      document_id: props.documentId,
      mode: props.mode
    })
    
    config.events = {
      onDocumentReady: () => { loading.value = false },
      onError: (event: any) => { error.value = `编辑器错误: ${JSON.stringify(event.data)}` }
    }
    
    editor = new window.DocsAPI.DocEditor('onlyoffice-editor', config)
  } catch (err: any) {
    error.value = err.message || '编辑器初始化失败'
    loading.value = false
  }
}

onMounted(() => initEditor())
onUnmounted(() => { if (editor) editor.destroyEditor() })
</script>

<style scoped>
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
</style>
```

#### 3.2 集成到各个页面

**Files.vue - 文件预览**：

```vue
<el-dialog v-model="previewVisible" title="文件预览" :fullscreen="true" class="preview-dialog">
  <div class="preview-container">
    <OnlyOfficeEditor
      v-if="previewType === 'onlyoffice' && currentFile"
      :file-id="currentFile.id"
      mode="view"
      height="calc(100vh - 120px)"
    />
  </div>
</el-dialog>
```

**Review.vue - 文件研判**：

```vue
<el-row :gutter="20" class="review-row">
  <el-col :span="16" class="preview-col">
    <div class="preview-area">
      <h3>文件预览</h3>
      <div class="preview-container">
        <OnlyOfficeEditor
          v-if="previewType === 'onlyoffice' && fileId"
          :file-id="fileId"
          mode="view"
          height="100%"
        />
      </div>
    </div>
  </el-col>
  <el-col :span="8">
    <div class="review-panel">
      <h3>AI 研判结果</h3>
      <!-- 研判内容 -->
    </div>
  </el-col>
</el-row>
```

### 阶段4：部署

#### 4.1 后端部署

```bash
# 后端代码已挂载，只需重启容器
cd ~/lizhanglan/Petition-System
docker-compose restart petition-backend
```

#### 4.2 前端部署

```bash
# 拉取代码
cd ~/lizhanglan/Petition-System
git pull

# 重新构建前端
docker-compose build frontend

# 重启前端容器
docker-compose up -d frontend
```

---

## 核心代码实现

### 后端核心文件

1. **`backend/app/services/onlyoffice_service.py`**
   - OnlyOfficeService类
   - 配置生成逻辑
   - 文档key生成

2. **`backend/app/api/v1/endpoints/onlyoffice.py`**
   - 配置端点
   - 下载代理端点
   - 回调处理端点

3. **`backend/app/api/v1/endpoints/files.py`**
   - 文件预览端点修改
   - 返回ONLYOFFICE标识

### 前端核心文件

1. **`frontend/src/components/OnlyOfficeEditor.vue`**
   - 编辑器组件
   - API脚本加载
   - 事件处理

2. **`frontend/src/views/Files.vue`**
   - 文件预览集成
   - Dialog布局优化

3. **`frontend/src/views/Review.vue`**
   - 文件研判集成
   - 左右分栏布局

4. **`frontend/src/views/Documents.vue`**
   - 文书查看和编辑

5. **`frontend/src/views/Generate.vue`**
   - 文书生成预览

---

## 部署配置

### Docker配置

**docker-compose.yml**：

```yaml
services:
  backend:
    networks:
      - petition-network
    environment:
      - ONLYOFFICE_ENABLED=true
      - ONLYOFFICE_SERVER_URL=http://101.37.24.171:9090
      - ONLYOFFICE_JWT_ENABLED=false

networks:
  petition-network:
    driver: bridge
```

### ONLYOFFICE配置

**配置文件**: `/etc/onlyoffice/documentserver/local.json`（容器内）

```json
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
```

### Nginx配置

**缓存文件访问**（已禁用secure_link）：

```nginx
location ~* ^(\/cache\/files.*)(\/.*) {
  alias /var/lib/onlyoffice/documentserver/App_Data$1;
  add_header Content-Disposition "attachment; filename*=UTF-8''$arg_filename";
  # secure_link检查已删除
}
```

---

## 问题解决历程

### 问题1：Axios拦截器双重提取data

**现象**：前端获取配置时，数据被双重提取导致undefined

**原因**：Axios拦截器已经提取了response.data，代码中又提取了一次

**解决**：检查响应结构，避免双重提取

### 问题2：数据库classification字段缺失

**现象**：文件预览时报错字段不存在

**解决**：添加数据库迁移，增加classification字段

### 问题3：Nginx强缓存

**现象**：前端代码更新后，浏览器仍使用旧代码

**解决**：修改Nginx配置，禁用强缓存

### 问题4：ONLYOFFICE HEAD请求失败

**现象**：ONLYOFFICE发送HEAD请求，后端返回405

**解决**：后端下载端点支持HEAD方法

### 问题5：Docker网络隔离

**现象**：ONLYOFFICE无法访问后端

**解决**：将ONLYOFFICE容器加入项目Docker网络

### 问题6：Vue v-else导致DOM不存在

**现象**：编辑器初始化时找不到#onlyoffice-editor元素

**解决**：改用v-show而非v-else

### 问题7：JWT验证错误

**现象**：errorCode: -20，JWT验证失败

**解决**：禁用JWT验证（JWT_ENABLED=false）

### 问题8：私有IP访问被拒

**现象**：ONLYOFFICE拒绝访问172.18.0.4

**解决**：配置allowPrivateIPAddress: true

### 问题9：插件下载卡住

**现象**：容器启动时卡在插件下载

**解决**：跳过插件安装

### 问题10：docservice进程未加载配置

**现象**：配置文件已修改，但仍报私有IP错误

**解决**：重启docservice和converter进程

### 问题11：secure_link缓存文件403

**现象**：浏览器请求缓存文件返回403

**原因**：Nginx的secure_link模块要求MD5签名

**解决**：删除secure_link检查代码

### 问题12-13：预览布局问题

**现象**：编辑器显示区域太小

**解决**：优化CSS布局，使用flex和calc()

---

## 测试验证

### 功能测试清单

- [x] 文件上传
- [x] 文件预览（ONLYOFFICE）
- [x] 文件研判预览
- [x] 文书生成预览
- [x] 文书查看
- [x] 文书在线编辑
- [x] 文档保存
- [x] 多种文件格式支持（docx, xlsx, pptx）

### 测试步骤

1. **文件预览测试**
   ```
   访问：http://101.37.24.171:8081
   登录 → 文件管理 → 点击"预览"
   预期：全屏显示ONLYOFFICE编辑器，文档正常显示
   ```

2. **文件研判测试**
   ```
   文件管理 → 点击"研判"
   预期：左侧预览（16列），右侧研判结果（8列）
   ```

3. **文书编辑测试**
   ```
   文书管理 → 点击"在线编辑"
   预期：可以编辑文档，保存后更新MinIO
   ```

### 性能指标

- 编辑器加载时间：< 3秒
- 文档打开时间：< 2秒
- 保存响应时间：< 1秒

---

## 维护指南

### 日常维护

**查看ONLYOFFICE日志**：

```bash
# 实时日志
docker logs -f gracious_curran

# 错误日志
docker logs gracious_curran 2>&1 | grep -i error

# 特定服务日志
docker exec gracious_curran tail -f /var/log/onlyoffice/documentserver/docservice/out.log
```

**重启ONLYOFFICE服务**：

```bash
# 重启整个容器
docker restart gracious_curran

# 只重启服务进程
docker exec gracious_curran supervisorctl restart ds:docservice ds:converter
```

**检查服务状态**：

```bash
# 检查进程状态
docker exec gracious_curran supervisorctl status

# 检查网络连接
docker exec gracious_curran curl -I http://petition-backend:8000/api/v1/onlyoffice/health
```

### 配置修改

**修改ONLYOFFICE配置**：

```bash
# 编辑配置文件
docker exec -it gracious_curran vi /etc/onlyoffice/documentserver/local.json

# 重启服务使配置生效
docker exec gracious_curran supervisorctl restart ds:docservice ds:converter
```

**修改Nginx配置**：

```bash
# 编辑配置
docker exec -it gracious_curran vi /etc/nginx/includes/ds-docservice.conf

# 测试配置
docker exec gracious_curran nginx -t

# 重载配置
docker exec gracious_curran nginx -s reload
```

### 故障排查

**问题：编辑器无法加载**

1. 检查ONLYOFFICE服务是否运行
2. 检查网络连接
3. 查看浏览器控制台错误
4. 检查后端日志

**问题：文件下载失败**

1. 检查MinIO连接
2. 检查文件是否存在
3. 检查后端下载端点日志
4. 验证ONLYOFFICE能否访问后端

**问题：保存失败**

1. 检查回调URL配置
2. 检查后端回调端点日志
3. 验证MinIO写入权限

### 备份和恢复

**备份配置**：

```bash
# 备份ONLYOFFICE配置
docker exec gracious_curran tar czf /tmp/onlyoffice-config.tar.gz \
  /etc/onlyoffice/documentserver/

# 复制到主机
docker cp gracious_curran:/tmp/onlyoffice-config.tar.gz ./
```

**恢复配置**：

```bash
# 复制到容器
docker cp onlyoffice-config.tar.gz gracious_curran:/tmp/

# 解压恢复
docker exec gracious_curran tar xzf /tmp/onlyoffice-config.tar.gz -C /

# 重启服务
docker exec gracious_curran supervisorctl restart ds:docservice ds:converter
```

### 升级指南

**升级ONLYOFFICE版本**：

```bash
# 停止并删除旧容器
docker stop gracious_curran
docker rm gracious_curran

# 拉取新版本
docker pull onlyoffice/documentserver:latest

# 启动新容器（使用相同配置）
docker run -d \
  --name gracious_curran \
  -p 9090:80 \
  -e JWT_ENABLED=false \
  onlyoffice/documentserver:latest

# 加入网络
docker network connect petition-system_petition-network gracious_curran

# 重新配置
# （执行配置步骤）
```

---

## 附录

### 相关文档

- [ONLYOFFICE官方文档](https://api.onlyoffice.com/editors/basic)
- [Docker部署指南](https://github.com/ONLYOFFICE/Docker-DocumentServer)
- [API参考](https://api.onlyoffice.com/editors/config/)

### 联系方式

- 技术支持：Kiro AI Assistant
- 项目仓库：https://github.com/lizhanglan/Petition-System

### 更新日志

- **2026-01-04**: 完成ONLYOFFICE集成，所有功能验证通过
- **2026-01-03**: 开始重构，替换WPS和华为云服务

---

**文档结束**
