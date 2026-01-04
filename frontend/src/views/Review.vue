<template>
  <div class="review-page">
    <!-- 降级状态通知 -->
    <FallbackNotice />
    
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>文件研判</span>
          <el-button @click="$router.back()">返回</el-button>
        </div>
      </template>
      
      <el-row :gutter="20" class="review-row">
        <el-col :span="16" class="preview-col">
          <div class="preview-area">
            <h3>文件预览</h3>
            
            <!-- ONLYOFFICE预览 -->
            <div v-if="previewType === 'onlyoffice' && fileId && !previewError" class="preview-container">
              <OnlyOfficeEditor
                :file-id="fileId"
                mode="view"
                height="100%"
                @error="handlePreviewError"
              />
            </div>
            
            <!-- 其他预览方式 -->
            <div v-else-if="previewUrl && !previewError">
              <iframe 
                :src="previewUrl" 
                class="preview-iframe" 
                @error="handlePreviewError"
                sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
              />
            </div>
            
            <!-- 错误提示 -->
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
            
            <!-- 加载中 -->
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
              <!-- 总体评价 -->
              <div class="summary-section">
                <h4>总体评价</h4>
                <div class="summary-content">
                  {{ reviewResult.summary }}
                </div>
              </div>
              
              <!-- 问题详情 -->
              <div v-if="reviewResult.errors && reviewResult.errors.length > 0" class="problems-section">
                <h4>发现 {{ reviewResult.errors.length }} 个问题</h4>
                <div class="problem-list">
                  <div
                    v-for="(error, index) in reviewResult.errors"
                    :key="index"
                    class="problem-item"
                  >
                    <div class="problem-number">{{ index + 1 }}.</div>
                    <div class="problem-content">
                      <p class="problem-text">{{ error.description || error }}</p>
                      <p v-if="error.suggestion" class="suggestion-text">
                        <span class="label">建议：</span>{{ error.suggestion }}
                      </p>
                      <p v-if="error.reference" class="reference-text">
                        <span class="label">依据：</span>{{ error.reference }}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 无问题状态 -->
              <div v-else class="no-problems">
                <p>✓ 未发现明显问题，文档质量良好</p>
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
import FallbackNotice from '@/components/FallbackNotice.vue'
import OnlyOfficeEditor from '@/components/OnlyOfficeEditor.vue'

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
  if (event.message && (
    event.message.includes('split is not a function') ||
    event.message.includes('Cannot read') ||
    event.message.includes('view.chigua.ren')
  )) {
    event.preventDefault()
    return false
  }
}

// 捕获 postMessage 错误
const handleMessageError = (event: MessageEvent) => {
  // 忽略华为云预览服务的消息错误
  if (event.data && typeof event.data === 'object') {
    // 只在开发环境输出调试信息
    if (import.meta.env.DEV) {
      console.debug('Preview service message:', event.data)
    }
  }
}

const loadPreview = async () => {
  // 验证fileId
  if (!fileId || isNaN(fileId)) {
    previewError.value = true
    ElMessage.error('无效的文件ID，请从文件列表重新进入')
    console.error('Invalid fileId:', fileId, 'from route params:', route.params.fileId)
    return
  }
  
  loading.value = true
  console.log('[Review] Loading preview for file:', fileId)
  
  try {
    const data: any = await getFilePreview(fileId)
    console.log('[Review] Preview data received:', data)
    
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
      // 检查是否是ONLYOFFICE标记
      if (data.preview_url === 'use_onlyoffice_component') {
        console.log('[Review] ONLYOFFICE preview detected')
        previewType.value = 'onlyoffice'
      } else {
        previewUrl.value = data.preview_url
        console.log('[Review] Preview URL set:', previewUrl.value)
      }
    }
  } catch (error: any) {
    console.error('[Review] Load preview error:', error)
    previewError.value = true
    
    // 更友好的错误提示
    if (error.response?.status === 404) {
      ElMessage.error('文件不存在或已被删除')
    } else if (error.response?.status === 422) {
      ElMessage.error('文件ID格式错误，请从文件列表重新进入')
    } else {
      ElMessage.error('加载预览失败: ' + (error.response?.data?.detail || error.message))
    }
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
    const result: any = await reviewDocument(fileId)
    reviewResult.value = result
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
  const map: Record<string, string> = {
    content: '内容错误',
    format: '格式错误',
    logic: '逻辑错误',
    grammar: '语法错误',
    style: '文风问题',
    compliance: '合规问题'
  }
  return map[type] || type
}

const getErrorLevel = (level: string) => {
  const map: Record<string, string> = {
    critical: '严重',
    high: '重要',
    medium: '一般',
    low: '轻微',
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

.review-row {
  height: calc(100vh - 200px);
}

.preview-col {
  height: 100%;
}

.preview-area {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.preview-area h3 {
  margin-bottom: 15px;
  color: #333;
  flex-shrink: 0;
}

.preview-container {
  flex: 1;
  min-height: 0;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

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
  height: calc(100vh - 200px);
  overflow-y: auto;
  padding: 20px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

/* 总体评价区域 */
.summary-section {
  margin-top: 20px;
  padding: 20px;
  background-color: white;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.summary-section h4 {
  margin: 0 0 15px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.summary-content {
  line-height: 1.8;
  color: #606266;
  font-size: 14px;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* 问题列表区域 */
.problems-section {
  margin-top: 20px;
  padding: 20px;
  background-color: white;
  border-radius: 8px;
  border-left: 4px solid #e6a23c;
}

.problems-section h4 {
  margin: 0 0 20px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.problem-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.problem-item {
  display: flex;
  gap: 12px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 6px;
  line-height: 1.8;
}

.problem-number {
  flex-shrink: 0;
  color: #909399;
  font-weight: 600;
  font-size: 14px;
}

.problem-content {
  flex: 1;
}

.problem-text {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 14px;
  line-height: 1.8;
}

.suggestion-text,
.reference-text {
  margin: 8px 0 0 0;
  color: #606266;
  font-size: 13px;
  line-height: 1.6;
}

.suggestion-text {
  color: #67c23a;
}

.reference-text {
  color: #909399;
  font-style: italic;
}

.label {
  font-weight: 600;
  margin-right: 4px;
}

/* 无问题状态 */
.no-problems {
  margin-top: 20px;
  padding: 40px 20px;
  background-color: white;
  border-radius: 8px;
  text-align: center;
  border-left: 4px solid #67c23a;
}

.no-problems p {
  margin: 0;
  color: #67c23a;
  font-size: 16px;
  font-weight: 500;
}

.errors {
  margin-top: 15px;
}
</style>
