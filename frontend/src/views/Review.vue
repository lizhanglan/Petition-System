<template>
  <div class="review-page">
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>文件研判</span>
          <el-button @click="$router.back()">返回</el-button>
        </div>
      </template>
      
      <el-row :gutter="20">
        <el-col :span="16">
          <div class="preview-area">
            <h3>文件预览</h3>
            <div v-if="previewUrl && !previewError">
              <iframe 
                :src="previewUrl" 
                class="preview-iframe" 
                @error="handlePreviewError"
                sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
              />
            </div>
            <div v-else-if="previewError" class="preview-error">
              <el-empty :description="getPreviewErrorMessage()">
                <el-space>
                  <el-button type="primary" @click="downloadFile">
                    <el-icon><Download /></el-icon>
                    下载文件
                  </el-button>
                  <el-button @click="loadPreview">
                    <el-icon><Refresh /></el-icon>
                    重新加载
                  </el-button>
                </el-space>
              </el-empty>
            </div>
            <el-empty v-else description="加载中..." />
          </div>
        </el-col>
        
        <el-col :span="8">
          <div class="review-panel">
            <h3>AI 研判结果</h3>
            
            <el-button type="primary" @click="handleReview" :loading="reviewing" style="width: 100%; margin-bottom: 20px;">
              开始研判
            </el-button>
            
            <div v-if="reviewResult">
              <el-alert
                :title="`发现 ${reviewResult.errors.length} 个问题`"
                :type="reviewResult.errors.length > 0 ? 'warning' : 'success'"
                :closable="false"
                style="margin-bottom: 20px;"
              />
              
              <div class="summary">
                <h4>总体评价</h4>
                <p>{{ reviewResult.summary }}</p>
              </div>
              
              <div v-if="reviewResult.errors.length > 0" class="errors">
                <h4>问题列表</h4>
                <el-collapse>
                  <el-collapse-item
                    v-for="(error, index) in reviewResult.errors"
                    :key="index"
                    :title="`${index + 1}. ${error.description}`"
                  >
                    <p><strong>类型：</strong>{{ getErrorType(error.type) }}</p>
                    <p><strong>级别：</strong>{{ getErrorLevel(error.level) }}</p>
                    <p><strong>建议：</strong>{{ error.suggestion }}</p>
                    <p v-if="error.reference"><strong>依据：</strong>{{ error.reference }}</p>
                  </el-collapse-item>
                </el-collapse>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { Download, Refresh } from '@element-plus/icons-vue'
import { getFilePreview } from '@/api/files'
import { reviewDocument } from '@/api/documents'
import { ElMessage } from 'element-plus'

const route = useRoute()
const fileId = Number(route.params.fileId)
const loading = ref(false)
const reviewing = ref(false)
const previewUrl = ref('')
const previewError = ref(false)
const previewType = ref('direct')
const fileName = ref('')
const fileType = ref('')
const reviewResult = ref<any>(null)
const fileUrl = ref('')

// 捕获 iframe 内部的错误，避免显示在控制台
const handleWindowError = (event: ErrorEvent) => {
  // 忽略来自华为云预览服务的错误
  if (event.message && event.message.includes('split is not a function')) {
    event.preventDefault()
    return false
  }
}

// 捕获 postMessage 错误
const handleMessageError = (event: MessageEvent) => {
  // 忽略华为云预览服务的消息错误
  console.debug('Preview service message:', event.data)
}

const loadPreview = async () => {
  loading.value = true
  try {
    const data = await getFilePreview(fileId)
    fileUrl.value = data.file_url || ''
    fileName.value = data.file_name || ''
    fileType.value = data.file_type || ''
    previewType.value = data.preview_type || 'direct'
    
    if (!data.preview_url) {
      previewError.value = true
      
      if (data.preview_type === 'unsupported') {
        if (data.file_type === 'docx' || data.file_type === 'doc') {
          ElMessage.warning('Word 文档预览服务暂时不可用，请下载文件查看。研判功能不受影响。')
        } else {
          ElMessage.warning('该文件格式暂不支持预览，请下载文件查看。研判功能不受影响。')
        }
      } else {
        ElMessage.warning('预览服务暂时不可用，但仍可进行研判')
      }
    } else {
      previewUrl.value = data.preview_url
      
      // 设置预览超时检测
      setTimeout(() => {
        if (!previewError.value && previewUrl.value) {
          console.log('Preview loaded successfully')
        }
      }, 5000)
    }
  } catch (error) {
    console.error(error)
    previewError.value = true
    ElMessage.error('加载预览失败')
  } finally {
    loading.value = false
  }
}

const handlePreviewError = () => {
  previewError.value = true
  ElMessage.warning('预览加载失败，请尝试下载文件查看')
}

const downloadFile = () => {
  if (fileUrl.value) {
    window.open(fileUrl.value, '_blank')
  } else {
    window.open(`/api/v1/files/${fileId}/download`, '_blank')
  }
}

const handleReview = async () => {
  reviewing.value = true
  try {
    ElMessage.info('正在进行 AI 研判，这可能需要 1-2 分钟，请耐心等待...')
    reviewResult.value = await reviewDocument(fileId)
    ElMessage.success('研判完成')
  } catch (error: any) {
    console.error(error)
    if (error.code === 'ECONNABORTED') {
      ElMessage.error('研判超时，请稍后重试。如果文件较大，可能需要更长时间处理。')
    } else {
      ElMessage.error('研判失败，请稍后重试')
    }
  } finally {
    reviewing.value = false
  }
}

const getErrorType = (type: string) => {
  const map: any = {
    content: '内容错误',
    format: '格式错误'
  }
  return map[type] || type
}

const getErrorLevel = (level: string) => {
  const map: any = {
    character: '字符级',
    sentence: '句子级',
    paragraph: '段落级'
  }
  return map[level] || level
}

const getPreviewErrorMessage = () => {
  if (previewType.value === 'unsupported') {
    if (fileType.value === 'docx' || fileType.value === 'doc') {
      return 'Word 文档预览服务暂时不可用\n您可以下载文件查看，或直接进行 AI 研判'
    }
    return '该文件格式暂不支持在线预览\n您可以下载文件查看，或直接进行 AI 研判'
  }
  return '预览加载失败\n您可以下载文件查看，或直接进行 AI 研判'
}

onMounted(() => {
  // 添加全局错误处理
  window.addEventListener('error', handleWindowError, true)
  window.addEventListener('message', handleMessageError)
  
  loadPreview()
})

onUnmounted(() => {
  // 移除全局错误处理
  window.removeEventListener('error', handleWindowError, true)
  window.removeEventListener('message', handleMessageError)
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.preview-area h3,
.review-panel h3 {
  margin-bottom: 15px;
  color: #333;
}

.preview-iframe {
  width: 100%;
  height: calc(100vh - 280px);
  border: 1px solid #e0e0e0;
  border-radius: 4px;
}

.preview-error {
  width: 100%;
  height: calc(100vh - 280px);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background-color: #f5f5f5;
}

.review-panel {
  height: calc(100vh - 280px);
  overflow-y: auto;
  padding: 20px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.summary,
.errors {
  margin-top: 20px;
  padding: 15px;
  background-color: white;
  border-radius: 4px;
}

.summary h4,
.errors h4 {
  margin-bottom: 10px;
  color: #333;
}

.summary p {
  line-height: 1.6;
  color: #666;
}

.errors {
  margin-top: 15px;
}
</style>
