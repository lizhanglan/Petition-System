<template>
  <div class="generate-page">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>AI 对话生成</span>
          </template>
          
          <div class="chat-container">
            <div class="messages" ref="messagesRef">
              <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
                <div class="message-content">{{ msg.content }}</div>
              </div>
            </div>
            
            <div class="input-area">
              <el-select v-model="selectedTemplateId" placeholder="选择模板" style="width: 200px; margin-bottom: 10px;">
                <el-option
                  v-for="template in templates"
                  :key="template.id"
                  :label="template.name"
                  :value="template.id"
                />
              </el-select>
              
              <el-input
                v-model="inputMessage"
                type="textarea"
                :rows="3"
                placeholder="请描述您的文书生成需求..."
                @keydown.ctrl.enter="handleSend"
              />
              
              <el-button type="primary" @click="handleSend" :loading="generating" style="margin-top: 10px; width: 100%">
                发送 (Ctrl+Enter)
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
              <el-button v-if="generatedContent" type="success" @click="handleSave">保存文书</el-button>
            </div>
          </template>
          
          <div class="preview-container">
            <div v-if="generatedContent" class="preview-content">
              {{ generatedContent }}
            </div>
            <el-empty v-else description="暂无生成内容" />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { getTemplateList } from '@/api/templates'
import { generateDocument } from '@/api/documents'
import { ElMessage } from 'element-plus'

const route = useRoute()
const templates = ref([])
const selectedTemplateId = ref<number | null>(null)
const messages = ref<any[]>([])
const inputMessage = ref('')
const generatedContent = ref('')
const generating = ref(false)
const messagesRef = ref()

const loadTemplates = async () => {
  try {
    templates.value = await getTemplateList()
    
    // 如果 URL 中有 templateId，自动选中
    if (route.query.templateId) {
      selectedTemplateId.value = Number(route.query.templateId)
    }
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
  
  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: inputMessage.value
  })
  
  const userInput = inputMessage.value
  inputMessage.value = ''
  
  // 滚动到底部
  await nextTick()
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
  
  // 调用 AI 生成
  generating.value = true
  try {
    const result = await generateDocument({
      template_id: selectedTemplateId.value,
      prompt: userInput,
      context: messages.value.slice(-20) // 最近10轮对话
    })
    
    generatedContent.value = result.content
    
    // 添加 AI 回复
    messages.value.push({
      role: 'assistant',
      content: '文书已生成，请在右侧查看预览'
    })
    
    ElMessage.success('生成成功')
  } catch (error) {
    console.error(error)
    messages.value.push({
      role: 'assistant',
      content: '生成失败，请重试'
    })
  } finally {
    generating.value = false
    
    // 滚动到底部
    await nextTick()
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  }
}

const handleSave = () => {
  ElMessage.success('文书已保存')
  // TODO: 实现保存逻辑
}

onMounted(() => {
  loadTemplates()
})
</script>

<style scoped>
.generate-page {
  height: calc(100vh - 140px);
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
  margin-bottom: 15px;
  display: flex;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.message-content {
  max-width: 70%;
  padding: 10px 15px;
  border-radius: 8px;
  word-wrap: break-word;
}

.message.user .message-content {
  background-color: #409EFF;
  color: white;
}

.message.assistant .message-content {
  background-color: white;
  color: #333;
  border: 1px solid #e0e0e0;
}

.input-area {
  padding: 10px;
  background-color: white;
  border-radius: 4px;
}

.preview-container {
  height: calc(100vh - 240px);
  overflow-y: auto;
  padding: 20px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.preview-content {
  background-color: white;
  padding: 30px;
  border-radius: 4px;
  white-space: pre-wrap;
  line-height: 1.8;
  font-size: 14px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
