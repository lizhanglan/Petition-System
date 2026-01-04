<template>
  <div class="document-edit-page">
    <el-card v-loading="loading">
      <template #header>
        <div class="header">
          <div class="header-left">
            <el-button @click="goBack" size="small">
              <el-icon><ArrowLeft /></el-icon>
              返回
            </el-button>
            <span class="title">编辑文书</span>
          </div>
          <div class="header-right">
            <el-button type="success" @click="handleSave" :loading="saving" size="small">
              保存
            </el-button>
            <el-dropdown @command="handleDownloadFormat" size="small">
              <el-button type="primary" size="small">
                下载<el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="pdf">下载为 PDF</el-dropdown-item>
                  <el-dropdown-item command="docx">下载为 Word</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </template>

      <div v-if="document" class="document-info">
        <el-form :model="document" label-width="100px">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="文书标题">
                <el-input v-model="document.title" placeholder="请输入文书标题" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="文书类型">
                <el-input v-model="document.document_type" readonly />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </div>

      <div class="editor-container">
        <OnlyOfficeEditor
          v-if="documentId"
          :document-id="documentId"
          mode="edit"
          height="calc(100vh - 280px)"
          @save="handleEditorSave"
          @error="handleEditorError"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, ArrowDown } from '@element-plus/icons-vue'
import OnlyOfficeEditor from '@/components/OnlyOfficeEditor.vue'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()

const documentId = ref<number>(0)
const document = ref<any>(null)
const loading = ref(false)
const saving = ref(false)

const loadDocument = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('token')
    const response = await fetch(`/api/v1/documents/${documentId.value}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (response.ok) {
      document.value = await response.json()
    } else {
      throw new Error('加载文书失败')
    }
  } catch (error: any) {
    console.error('Load document error:', error)
    ElMessage.error(error.message || '加载文书失败')
  } finally {
    loading.value = false
  }
}

const handleSave = async () => {
  saving.value = true
  try {
    const token = localStorage.getItem('token')
    const response = await fetch(`/api/v1/documents/${documentId.value}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        title: document.value.title,
        change_description: '在线编辑保存'
      })
    })
    
    if (response.ok) {
      ElMessage.success('保存成功')
    } else {
      throw new Error('保存失败')
    }
  } catch (error: any) {
    console.error('Save error:', error)
    ElMessage.error(error.message || '保存失败')
  } finally {
    saving.value = false
  }
}

const handleEditorSave = () => {
  ElMessage.success('文档已自动保存')
}

const handleEditorError = (error: string) => {
  console.error('Editor error:', error)
  ElMessage.error('编辑器加载失败')
}

const handleDownloadFormat = async (format: string) => {
  try {
    const token = localStorage.getItem('token')
    if (!token) {
      ElMessage.error('未登录，请先登录')
      return
    }
    
    const response = await fetch(`/api/v1/documents/${documentId.value}/download?format=${format}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (!response.ok) {
      throw new Error(`下载失败: ${response.status}`)
    }
    
    const contentDisposition = response.headers.get('Content-Disposition')
    const extension = format === 'pdf' ? 'pdf' : 'docx'
    let filename = `${document.value?.title || 'document'}.${extension}`
    if (contentDisposition) {
      const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(contentDisposition)
      if (matches && matches[1]) {
        filename = matches[1].replace(/['"]/g, '')
      }
    }
    
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    
    ElMessage.success(`${format === 'pdf' ? 'PDF' : 'Word'}文档下载成功`)
  } catch (error: any) {
    console.error('Download error:', error)
    ElMessage.error(`下载失败: ${error.message}`)
  }
}

const goBack = () => {
  router.back()
}

onMounted(() => {
  const id = route.params.id
  if (id) {
    documentId.value = Number(id)
    loadDocument()
  } else {
    ElMessage.error('文书ID无效')
    router.push('/documents')
  }
})
</script>

<style scoped>
.document-edit-page {
  padding: 20px;
  height: 100vh;
  overflow: hidden;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.title {
  font-size: 18px;
  font-weight: 500;
}

.header-right {
  display: flex;
  gap: 10px;
}

.document-info {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.editor-container {
  background-color: white;
  border-radius: 4px;
  overflow: hidden;
}
</style>
