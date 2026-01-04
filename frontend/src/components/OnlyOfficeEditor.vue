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
import request from '../api/request'

interface Props {
  fileId?: number
  documentId?: number
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

// 声明全局DocsAPI类型
declare global {
  interface Window {
    DocsAPI: any
  }
}

// 加载ONLYOFFICE API脚本
const loadOnlyOfficeScript = (): Promise<void> => {
  return new Promise((resolve, reject) => {
    console.log('[OnlyOffice] Loading API script...')
    
    // 检查是否已加载
    if (window.DocsAPI) {
      console.log('[OnlyOffice] API already loaded')
      resolve()
      return
    }
    
    // 检查是否已有script标签
    const existingScript = document.querySelector('script[src*="api/documents/api.js"]')
    if (existingScript) {
      console.log('[OnlyOffice] Script tag already exists, waiting for load...')
      // 等待加载完成
      const checkInterval = setInterval(() => {
        if (window.DocsAPI) {
          clearInterval(checkInterval)
          console.log('[OnlyOffice] API loaded from existing script')
          resolve()
        }
      }, 100)
      
      // 10秒超时
      setTimeout(() => {
        clearInterval(checkInterval)
        if (!window.DocsAPI) {
          reject(new Error('Timeout waiting for ONLYOFFICE API'))
        }
      }, 10000)
      return
    }
    
    console.log('[OnlyOffice] Creating script tag...')
    const script = document.createElement('script')
    script.src = 'http://101.37.24.171:9090/web-apps/apps/api/documents/api.js'
    script.type = 'text/javascript'
    
    script.onload = () => {
      console.log('[OnlyOffice] Script loaded successfully')
      // 等待DocsAPI可用
      const checkAPI = setInterval(() => {
        if (window.DocsAPI) {
          clearInterval(checkAPI)
          console.log('[OnlyOffice] DocsAPI is ready')
          resolve()
        }
      }, 50)
      
      // 5秒超时
      setTimeout(() => {
        clearInterval(checkAPI)
        if (!window.DocsAPI) {
          reject(new Error('DocsAPI not available after script load'))
        }
      }, 5000)
    }
    
    script.onerror = (error) => {
      console.error('[OnlyOffice] Script load error:', error)
      reject(new Error('Failed to load ONLYOFFICE API script'))
    }
    
    console.log('[OnlyOffice] Appending script to head...')
    document.head.appendChild(script)
    console.log('[OnlyOffice] Script tag appended')
  })
}

// 初始化编辑器
const initEditor = async () => {
  try {
    loading.value = true
    error.value = ''
    
    // 验证参数
    if (!props.fileId && !props.documentId) {
      throw new Error('必须提供fileId或documentId')
    }
    
    // 加载API脚本
    await loadOnlyOfficeScript()
    
    // 获取编辑器配置
    // 注意：request拦截器已经返回了response.data，所以这里直接就是配置对象
    console.log('[OnlyOffice] Requesting config with:', {
      file_id: props.fileId,
      document_id: props.documentId,
      mode: props.mode
    })
    
    const config = await request.post('/onlyoffice/config', {
      file_id: props.fileId,
      document_id: props.documentId,
      mode: props.mode
    })
    
    console.log('[OnlyOffice] Raw response:', config)
    console.log('[OnlyOffice] Response type:', typeof config)
    console.log('[OnlyOffice] Response keys:', config ? Object.keys(config) : 'null/undefined')
    
    // 检查是否需要再次提取data
    if (config && config.data && typeof config.data === 'object') {
      console.warn('[OnlyOffice] WARNING: Response has .data property, extracting it')
      const actualConfig = config.data
      console.log('[OnlyOffice] Actual config after extraction:', actualConfig)
      actualConfig.events = {
        onDocumentReady: () => {
          console.log('[OnlyOffice] Document ready')
          loading.value = false
        },
        onError: (event: any) => {
          console.error('[OnlyOffice] Error:', event)
          error.value = `编辑器错误: ${JSON.stringify(event.data)}`
          emit('error', error.value)
        },
        onWarning: (event: any) => {
          console.warn('[OnlyOffice] Warning:', event)
        },
        onInfo: (event: any) => {
          console.log('[OnlyOffice] Info:', event)
        }
      }
      
      // 初始化编辑器
      editor = new window.DocsAPI.DocEditor('onlyoffice-editor', actualConfig)
      console.log('[OnlyOffice] Editor initialized with extracted config')
      return
    }
    
    console.log('[OnlyOffice] Using config directly (no .data property)')
    
    // 验证config不是undefined
    if (!config || typeof config !== 'object') {
      throw new Error(`Invalid config received: ${JSON.stringify(config)}`)
    }
    
    // 添加事件处理
    config.events = {
      onDocumentReady: () => {
        console.log('[OnlyOffice] ✅ Document ready - hiding loading')
        loading.value = false
      },
      onError: (event: any) => {
        console.error('[OnlyOffice] ❌ Error event:', event)
        error.value = `编辑器错误: ${JSON.stringify(event.data)}`
        loading.value = false
        emit('error', error.value)
      },
      onWarning: (event: any) => {
        console.warn('[OnlyOffice] ⚠️  Warning event:', event)
      },
      onInfo: (event: any) => {
        console.log('[OnlyOffice] ℹ️  Info event:', event)
      },
      onAppReady: () => {
        console.log('[OnlyOffice] ✅ App ready')
      },
      onDocumentStateChange: (event: any) => {
        console.log('[OnlyOffice] 📄 Document state change:', event)
      },
      onRequestEditRights: () => {
        console.log('[OnlyOffice] 🔒 Request edit rights')
      }
    }
    
    // 初始化编辑器
    console.log('[OnlyOffice] Creating DocEditor with config:', config)
    editor = new window.DocsAPI.DocEditor('onlyoffice-editor', config)
    console.log('[OnlyOffice] Editor initialized, waiting for events...')
    
    // 设置超时，如果30秒后还在loading，强制隐藏
    setTimeout(() => {
      if (loading.value) {
        console.warn('[OnlyOffice] ⚠️  Timeout: Document not ready after 30s, hiding loading anyway')
        loading.value = false
      }
    }, 30000)
    
  } catch (err: any) {
    console.error('[OnlyOffice] Init error:', err)
    error.value = err.detail || err.message || '编辑器初始化失败'
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
