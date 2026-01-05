<template>
  <div class="docx-preview-container" ref="containerRef">
    <div v-if="loading" class="loading-state">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>正在加载文档...</span>
    </div>
    <div v-if="error" class="error-state">
      <el-empty :description="error">
        <el-button type="primary" @click="reload">
          重新加载
        </el-button>
      </el-empty>
    </div>
    <div 
      ref="previewRef" 
      class="docx-content"
      v-show="!loading && !error"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { renderAsync } from 'docx-preview'

interface Props {
  // 文件ID - 用于从服务器获取文件
  fileId?: number
  // 文档ID - 用于从服务器获取生成的文档
  documentId?: number
  // 直接传入的 Blob 数据
  blob?: Blob
  // 文件URL - 直接从URL加载
  fileUrl?: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  error: [error: string]
  loaded: []
}>()

const containerRef = ref<HTMLElement>()
const previewRef = ref<HTMLElement>()
const loading = ref(true)
const error = ref('')

// 加载并渲染文档
const loadDocument = async () => {
  loading.value = true
  error.value = ''

  try {
    let docBlob: Blob | null = null

    // 优先使用直接传入的 blob
    if (props.blob) {
      docBlob = props.blob
    }
    // 其次使用 fileUrl
    else if (props.fileUrl) {
      const response = await fetch(props.fileUrl)
      if (!response.ok) {
        throw new Error(`文件下载失败: ${response.status}`)
      }
      docBlob = await response.blob()
    }
    // 使用 fileId 从服务器获取
    else if (props.fileId) {
      const token = localStorage.getItem('token')
      const response = await fetch(`/api/v1/files/${props.fileId}/content`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (!response.ok) {
        throw new Error(`文件下载失败: ${response.status}`)
      }
      docBlob = await response.blob()
    }
    // 使用 documentId 从服务器获取
    else if (props.documentId) {
      const token = localStorage.getItem('token')
      const response = await fetch(`/api/v1/documents/${props.documentId}/download?format=docx`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (!response.ok) {
        throw new Error(`文档下载失败: ${response.status}`)
      }
      docBlob = await response.blob()
    }
    else {
      throw new Error('请提供 fileId、documentId、blob 或 fileUrl')
    }

    if (!docBlob) {
      throw new Error('无法获取文档内容')
    }

    // 检查是否是有效的 docx 文件
    const arrayBuffer = await docBlob.arrayBuffer()
    
    // 清空预览容器
    if (previewRef.value) {
      previewRef.value.innerHTML = ''
      
      // 渲染 docx - 使用与原始文档一致的样式
      await renderAsync(arrayBuffer, previewRef.value, undefined, {
        className: 'docx-wrapper',
        inWrapper: true,
        ignoreWidth: false,
        ignoreHeight: false,
        ignoreFonts: false,
        breakPages: true,
        ignoreLastRenderedPageBreak: true,
        experimental: false,
        trimXmlDeclaration: true,
        useBase64URL: true,
        renderHeaders: true,
        renderFooters: true,
        renderFootnotes: true,
        renderEndnotes: true
      })
      
      // 添加红头横线（docx-preview 不支持 VML 元素）
      addHeaderLines(previewRef.value)
      
      emit('loaded')
    }
  } catch (err: any) {
    console.error('[DocxPreview] Error:', err)
    error.value = err.message || '文档加载失败'
    emit('error', error.value)
  } finally {
    loading.value = false
  }
}

const reload = () => {
  loadDocument()
}

// 添加红头横线（补偿 docx-preview 不支持 VML 的问题）
const addHeaderLines = (container: HTMLElement) => {
  try {
    console.log('[DocxPreview] 开始添加红头横线')
    
    // 等待 DOM 完全渲染
    setTimeout(() => {
      // 尝试多种选择器找到文档容器
      let docContainer = container.querySelector('.docx-wrapper') as HTMLElement
      if (!docContainer) {
        docContainer = container.querySelector('section') as HTMLElement
      }
      if (!docContainer) {
        docContainer = container.querySelector('.docx-content') as HTMLElement
      }
      if (!docContainer) {
        docContainer = container
      }
      
      console.log('[DocxPreview] 文档容器:', docContainer.className || 'root')
      
      // 查找红头段落（第一个包含红色文字的段落）
      const paragraphs = docContainer.querySelectorAll('p')
      console.log('[DocxPreview] 找到段落数:', paragraphs.length)
      
      let headerParagraph: HTMLElement | null = null
      
      for (let i = 0; i < Math.min(5, paragraphs.length); i++) {
        const para = paragraphs[i] as HTMLElement
        const text = para.textContent || ''
        console.log(`[DocxPreview] 段落 ${i + 1}:`, text.substring(0, 30))
        
        const spans = para.querySelectorAll('span')
        
        // 检查是否有红色文字
        const hasRedText = Array.from(spans).some(span => {
          const color = window.getComputedStyle(span).color
          const isRed = color.includes('255, 0, 0') || color.includes('192, 0, 0')
          if (isRed) {
            console.log('[DocxPreview] 找到红色文字')
          }
          return isRed
        })
        
        if (hasRedText || text.includes('学生工作部') || text.includes('工作处')) {
          headerParagraph = para
          console.log('[DocxPreview] 找到红头段落')
          break
        }
      }
      
      // 创建红头横线容器
      const lineContainer = document.createElement('div')
      lineContainer.className = 'header-lines-overlay'
      lineContainer.style.cssText = `
        position: absolute;
        left: 0;
        right: 0;
        top: 0;
        width: 100%;
        pointer-events: none;
        z-index: 1;
      `
      
      // 计算横线位置
      let line1Top = 80 // 默认位置
      let line2Top = 1000 // 默认位置（页面底部）
      
      if (headerParagraph) {
        try {
          const containerRect = docContainer.getBoundingClientRect()
          const paraRect = headerParagraph.getBoundingClientRect()
          
          // 第一条线在红头段落正下方
          line1Top = paraRect.bottom - containerRect.top + 5
          // 第二条线在页面底部（约 1000px，接近 A4 纸底部）
          line2Top = 1000
          
          console.log('[DocxPreview] 横线位置:', { line1Top, line2Top })
        } catch (err) {
          console.warn('[DocxPreview] 计算位置失败，使用默认值:', err)
        }
      } else {
        console.log('[DocxPreview] 未找到红头段落，使用默认位置')
      }
      
      // 第一条横线（红头正下方）
      const line1 = document.createElement('div')
      line1.style.cssText = `
        position: absolute;
        left: 50px;
        right: 50px;
        top: ${line1Top}px;
        height: 3px;
        background: #ff0000;
        box-shadow: 0 1px 2px rgba(255, 0, 0, 0.3);
      `
      
      lineContainer.appendChild(line1)
      // 不再添加第二条横线
      
      // 确保容器是相对定位
      if (window.getComputedStyle(docContainer).position === 'static') {
        docContainer.style.position = 'relative'
      }
      
      docContainer.appendChild(lineContainer)
      console.log('[DocxPreview] 红头横线已添加')
    }, 300) // 延迟 300ms 确保 DOM 和样式完全渲染
    
  } catch (err) {
    console.error('[DocxPreview] 添加红头横线失败:', err)
  }
}

// 监听 props 变化
watch(
  () => [props.fileId, props.documentId, props.blob, props.fileUrl],
  () => {
    loadDocument()
  }
)

onMounted(() => {
  loadDocument()
})

// 暴露方法
defineExpose({
  reload
})
</script>

<style scoped>
.docx-preview-container {
  width: 100%;
  height: 100%;
  overflow: auto;
  background-color: #f5f5f5;
  position: relative;
  text-align: left; /* 覆盖全局 #app 的 text-align: center */
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 12px;
  color: #666;
}

.loading-state .el-icon {
  font-size: 32px;
  color: #409eff;
}

.docx-content {
  min-height: 100%;
  padding: 20px;
  background: white;
}

/* docx-preview 生成的样式 - 保持原始对齐 */
.docx-content :deep(.docx-wrapper) {
  background: white;
  padding: 20px 40px;
  /* 不设置 margin: 0 auto 或 text-align: center */
}

.docx-content :deep(.docx-wrapper > section) {
  padding: 30px 50px;
  margin-bottom: 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  background: white;
  /* 不设置 text-align，保持文档原始对齐 */
}

/* 确保段落保持原始对齐 */
.docx-content :deep(p) {
  /* 不强制设置 text-align */
}

/* 确保表格正确显示 */
.docx-content :deep(table) {
  border-collapse: collapse;
}

.docx-content :deep(td),
.docx-content :deep(th) {
  border: 1px solid #ddd;
  padding: 8px;
}

/* 确保图片不溢出 */
.docx-content :deep(img) {
  max-width: 100%;
  height: auto;
}
</style>
