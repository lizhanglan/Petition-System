<template>
  <div class="generate-page">
    <!-- 降级状态通知 -->
    <FallbackNotice />
    
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>AI 对话生成</span>
              <div class="header-actions">
                <el-tag v-if="sessionInfo.message_count > 0" type="info" size="small">
                  {{ sessionInfo.message_count }} 条消息
                </el-tag>
                <el-button size="small" @click="handleClearHistory" :disabled="messages.length === 0">
                  清除历史
                </el-button>
              </div>
            </div>
          </template>
          
          <div class="chat-container">
            <div class="messages" ref="messagesRef">
              <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
                <div class="message-avatar">
                  <el-icon v-if="msg.role === 'user'"><User /></el-icon>
                  <el-icon v-else><ChatDotRound /></el-icon>
                </div>
                <div class="message-content">
                  <div class="message-text">{{ msg.content }}</div>
                  <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
                </div>
              </div>
              
              <div v-if="generating" class="message assistant">
                <div class="message-avatar">
                  <el-icon><ChatDotRound /></el-icon>
                </div>
                <div class="message-content">
                  <div class="message-text">
                    <el-icon class="is-loading"><Loading /></el-icon>
                    正在生成中...
                  </div>
                </div>
              </div>
            </div>
            
            <div class="input-area">
              <!-- 文件引用 -->
              <div v-if="fileReferences.length > 0" class="file-references">
                <el-tag
                  v-for="fileId in fileReferences"
                  :key="fileId"
                  closable
                  @close="removeFileReference(fileId)"
                  size="small"
                  style="margin-right: 5px"
                >
                  文件 #{{ fileId }}
                </el-tag>
              </div>
              
              <div class="input-controls">
                <el-select 
                  v-model="selectedTemplateId" 
                  placeholder="选择模板" 
                  style="width: 200px;"
                  size="small"
                >
                  <el-option
                    v-for="template in templates"
                    :key="template.id"
                    :label="template.name"
                    :value="template.id"
                  />
                </el-select>
                
                <el-button 
                  size="small" 
                  @click="showFileSelector = true"
                  :disabled="generating"
                >
                  <el-icon><Paperclip /></el-icon>
                  引用文件
                </el-button>
              </div>
              
              <el-input
                v-model="inputMessage"
                type="textarea"
                :rows="3"
                placeholder="请描述您的文书生成需求...&#10;提示：可以引用已上传的文件作为参考"
                @keydown.ctrl.enter="handleSend"
                :disabled="generating"
              />
              
              <el-button 
                type="primary" 
                @click="handleSend" 
                :loading="generating" 
                style="margin-top: 10px; width: 100%"
              >
                {{ generating ? '生成中...' : '发送 (Ctrl+Enter)' }}
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>生成预览</span>
              <div v-if="currentDocumentId">
                <el-button type="success" @click="handleSave" size="small">保存文书</el-button>
                <el-button type="primary" @click="handleDownload" size="small">下载</el-button>
              </div>
            </div>
          </template>
          
          <div class="preview-container">
            <!-- ONLYOFFICE预览 - 可编辑模式 -->
            <OnlyOfficeEditor
              v-if="previewType === 'onlyoffice' && currentDocumentId"
              :document-id="currentDocumentId"
              mode="edit"
              height="calc(100vh - 240px)"
              @error="handlePreviewError"
            />
            
            <!-- 文档预览iframe -->
            <div v-else-if="previewUrl" class="document-preview">
              <iframe 
                :src="previewUrl" 
                frameborder="0" 
                width="100%" 
                height="100%"
                style="border-radius: 4px;"
              ></iframe>
            </div>
            
            <!-- 空状态 -->
            <el-empty v-else description="暂无生成内容">
              <template #image>
                <el-icon :size="60"><Document /></el-icon>
              </template>
              <template #description>
                <p>请在左侧输入需求并生成文书</p>
                <p style="font-size: 12px; color: #999; margin-top: 5px;">
                  生成后将在此处显示文档预览
                </p>
              </template>
            </el-empty>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 文件选择对话框 -->
    <el-dialog v-model="showFileSelector" title="选择参考文件" width="600px">
      <el-table :data="fileList" @selection-change="handleFileSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="file_name" label="文件名" />
        <el-table-column prop="file_type" label="类型" width="80" />
        <el-table-column prop="created_at" label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
      
      <template #footer>
        <el-button @click="showFileSelector = false">取消</el-button>
        <el-button type="primary" @click="confirmFileSelection">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { User, ChatDotRound, Loading, Paperclip, Document } from '@element-plus/icons-vue'
import { getTemplateList } from '@/api/templates'
import { getFileList } from '@/api/files'
import { 
  generateDocument, 
  getConversationHistory, 
  clearConversation
} from '@/api/documents'
import { ElMessage, ElMessageBox } from 'element-plus'
import FallbackNotice from '@/components/FallbackNotice.vue'
import OnlyOfficeEditor from '@/components/OnlyOfficeEditor.vue'

const route = useRoute()
const templates = ref<any[]>([])
const fileList = ref<any[]>([])
const selectedTemplateId = ref<number | null>(null)
const messages = ref<any[]>([])
const inputMessage = ref('')
const generatedContent = ref('')
const previewUrl = ref('')
const previewType = ref('')
const generating = ref(false)
const messagesRef = ref()
const showFileSelector = ref(false)
const fileReferences = ref<number[]>([])
const selectedFiles = ref<any[]>([])
const sessionId = ref<string>('')
const sessionInfo = ref<any>({
  message_count: 0,
  file_reference_count: 0
})
const currentDocumentId = ref<number | null>(null)

// 生成会话ID
const generateSessionId = () => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

const loadTemplates = async () => {
  try {
    const data: any = await getTemplateList()
    templates.value = data
    
    // 如果 URL 中有 templateId，自动选中
    if (route.query.templateId) {
      selectedTemplateId.value = Number(route.query.templateId)
    }
  } catch (error) {
    console.error(error)
  }
}

const loadFiles = async () => {
  try {
    const data: any = await getFileList()
    fileList.value = data
  } catch (error) {
    console.error(error)
  }
}

const loadConversationHistory = async () => {
  try {
    const data: any = await getConversationHistory(sessionId.value)
    messages.value = data.messages || []
    sessionInfo.value = data.session_info || {}
    
    // 滚动到底部
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error(error)
  }
}

const handleSend = async () => {
  if (!inputMessage.value.trim()) {
    ElMessage.warning('请输入内容')
    return
  }
  
  if (!selectedTemplateId.value) {
    ElMessage.warning('请选择模板')
    return
  }
  
  const userInput = inputMessage.value
  inputMessage.value = ''
  
  // 添加用户消息到界面
  messages.value.push({
    role: 'user',
    content: userInput,
    timestamp: new Date().toISOString()
  })
  
  // 滚动到底部
  await nextTick()
  scrollToBottom()
  
  // 调用 AI 生成
  generating.value = true
  try {
    const result: any = await generateDocument({
      template_id: selectedTemplateId.value,
      prompt: userInput,
      session_id: sessionId.value,
      file_references: fileReferences.value.length > 0 ? fileReferences.value : undefined
    })
    
    generatedContent.value = result.content
    currentDocumentId.value = result.id
    
    // 获取文档预览URL
    if (result.preview_url) {
      // 检查是否是ONLYOFFICE预览
      if (result.preview_url === 'use_onlyoffice_component') {
        previewType.value = 'onlyoffice'
        console.log('[Generate] Using ONLYOFFICE component for preview')
      } else {
        previewUrl.value = result.preview_url
        previewType.value = 'direct'
        console.log('[Generate] Preview URL:', result.preview_url)
      }
    } else {
      console.warn('[Generate] No preview_url in response, trying to fetch...')
      // 如果没有返回preview_url，尝试获取预览
      try {
        const previewResponse: any = await fetch(`/api/v1/documents/${result.id}/preview`)
        const previewData = await previewResponse.json()
        if (previewData.preview_url) {
          if (previewData.preview_url === 'use_onlyoffice_component') {
            previewType.value = 'onlyoffice'
            console.log('[Generate] Fetched ONLYOFFICE preview')
          } else {
            previewUrl.value = previewData.preview_url
            previewType.value = 'direct'
            console.log('[Generate] Fetched preview URL:', previewData.preview_url)
          }
        }
      } catch (error) {
        console.error('[Generate] Failed to fetch preview:', error)
      }
    }
    
    // 提取AI返回的chat_message和suggestions
    let chatMessage = `文书已生成（${result.content.length} 字），请在右侧查看预览。`
    
    if (result.ai_annotations) {
      // 使用AI返回的chat_message
      if (result.ai_annotations.chat_message) {
        chatMessage = result.ai_annotations.chat_message
      }
      
      // 如果有摘要，添加到消息中
      if (result.ai_annotations.summary) {
        chatMessage += `\n\n📝 摘要：${result.ai_annotations.summary}`
      }
      
      // 如果有建议，添加到消息中
      if (result.ai_annotations.suggestions && result.ai_annotations.suggestions.length > 0) {
        chatMessage += '\n\n💡 建议：'
        result.ai_annotations.suggestions.forEach((suggestion: string, index: number) => {
          chatMessage += `\n${index + 1}. ${suggestion}`
        })
      }
    }
    
    // 添加 AI 回复
    messages.value.push({
      role: 'assistant',
      content: chatMessage,
      timestamp: new Date().toISOString()
    })
    
    // 更新会话信息
    sessionInfo.value.message_count = messages.value.length
    
    ElMessage.success('生成成功')
  } catch (error: any) {
    console.error(error)
    messages.value.push({
      role: 'assistant',
      content: '生成失败，请重试。错误信息：' + (error.message || '未知错误'),
      timestamp: new Date().toISOString()
    })
    ElMessage.error('生成失败')
  } finally {
    generating.value = false
    
    // 滚动到底部
    await nextTick()
    scrollToBottom()
  }
}

const handleClearHistory = async () => {
  try {
    await ElMessageBox.confirm('确定要清除对话历史吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await clearConversation(sessionId.value)
    messages.value = []
    generatedContent.value = ''
    previewUrl.value = ''
    previewType.value = ''
    currentDocumentId.value = null
    fileReferences.value = []
    sessionInfo.value = { message_count: 0, file_reference_count: 0 }
    
    ElMessage.success('对话历史已清除')
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}

const handleFileSelectionChange = (selection: any[]) => {
  selectedFiles.value = selection
}

const confirmFileSelection = () => {
  fileReferences.value = selectedFiles.value.map(f => f.id)
  showFileSelector.value = false
  ElMessage.success(`已添加 ${fileReferences.value.length} 个文件引用`)
}

const removeFileReference = (fileId: number) => {
  fileReferences.value = fileReferences.value.filter(id => id !== fileId)
}

const handleSave = () => {
  if (currentDocumentId.value) {
    ElMessage.success('文书已自动保存')
  } else {
    ElMessage.warning('没有可保存的文书')
  }
}

const handleDownload = () => {
  if (currentDocumentId.value) {
    window.open(`/api/v1/documents/${currentDocumentId.value}/download?format=pdf`, '_blank')
  } else {
    ElMessage.warning('没有可下载的文书')
  }
}

const scrollToBottom = () => {
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

const formatTime = (timestamp: string) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

const handlePreviewError = (error: string) => {
  console.error('[Generate] Preview error:', error)
  ElMessage.error('预览加载失败')
}

onMounted(() => {
  // 生成会话ID
  sessionId.value = generateSessionId()
  
  loadTemplates()
  loadFiles()
  loadConversationHistory()
})
</script>

<style scoped>
.generate-page {
  height: calc(100vh - 140px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 240px);
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: #f5f5f5;
  border-radius: 4px;
  margin-bottom: 20px;
}

.message {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message.user .message-avatar {
  background-color: #409EFF;
  color: white;
}

.message.assistant .message-avatar {
  background-color: #67C23A;
  color: white;
}

.message-content {
  max-width: 70%;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.message.user .message-content {
  align-items: flex-end;
}

.message-text {
  padding: 12px 16px;
  border-radius: 12px;
  word-wrap: break-word;
  line-height: 1.6;
  white-space: pre-wrap;
}

.message.user .message-text {
  background-color: #409EFF;
  color: white;
  border-bottom-right-radius: 4px;
}

.message.assistant .message-text {
  background-color: white;
  color: #333;
  border: 1px solid #e0e0e0;
  border-bottom-left-radius: 4px;
}

.message-time {
  font-size: 12px;
  color: #999;
  padding: 0 8px;
}

.input-area {
  padding: 15px;
  background-color: white;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
}

.file-references {
  margin-bottom: 10px;
  padding: 8px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.input-controls {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.preview-container {
  height: calc(100vh - 240px);
  overflow: hidden;
  background-color: #f5f5f5;
  border-radius: 4px;
  position: relative;
}

.document-preview {
  width: 100%;
  height: 100%;
  background-color: white;
  border-radius: 4px;
  overflow: hidden;
}

.document-preview iframe {
  width: 100%;
  height: 100%;
}

.preview-content {
  background-color: white;
  padding: 30px;
  border-radius: 4px;
  white-space: pre-wrap;
  line-height: 1.8;
  font-size: 14px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  height: 100%;
  overflow-y: auto;
}
</style>
