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
    editor = new window.DocsAPI.DocEditor('onlyoffice-editor', config)
    console.log('[OnlyOffice] Editor initialized')
    
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
