<template>
  <div class="documents-page">
    <el-card>
      <template #header>
        <span>文书管理</span>
      </template>
      
      <el-table :data="documentList" v-loading="loading">
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="document_type" label="类型" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="密级" width="100">
          <template #default="{ row }">
            <el-tag 
              :color="getClassificationColor(row.classification)" 
              size="small"
              style="cursor: pointer"
              @click="handleClassification(row)"
            >
              {{ getClassificationText(row.classification) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="320">
          <template #default="{ row }">
            <el-button-group>
              <el-button size="small" @click="handleView(row)">查看</el-button>
              <el-button size="small" type="primary" @click="handleEdit(row)">编辑</el-button>
              <el-button size="small" type="success" @click="handleOnlineEdit(row)">在线编辑</el-button>
              <el-button size="small" type="info" @click="handleVersions(row)">版本</el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 文书详情对话框 -->
    <el-dialog 
      v-model="viewVisible" 
      title="文书详情" 
      width="90%" 
      top="5vh"
      destroy-on-close
    >
      <div v-if="currentDocument" class="document-detail">
        <!-- 文书信息 -->
        <el-descriptions :column="2" border style="margin-bottom: 20px">
          <el-descriptions-item label="标题">
            {{ currentDocument.title }}
          </el-descriptions-item>
          <el-descriptions-item label="文书类型">
            {{ currentDocument.document_type }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentDocument.status)">
              {{ getStatusText(currentDocument.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="密级">
            <el-tag :color="getClassificationColor(currentDocument.classification)">
              {{ getClassificationText(currentDocument.classification) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">
            {{ formatDate(currentDocument.created_at) }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 文书预览 -->
        <el-divider>文书预览</el-divider>
        <div class="document-preview-container">
          <div v-if="previewLoading" class="preview-loading">
            <el-icon :size="40" class="is-loading">
              <Loading />
            </el-icon>
            <p>正在加载预览...</p>
          </div>
          
          <!-- ONLYOFFICE预览 -->
          <OnlyOfficeEditor
            v-else-if="previewType === 'onlyoffice' && currentDocument"
            :document-id="currentDocument.id"
            mode="view"
            height="600px"
            @error="handlePreviewError"
          />
          
          <!-- 其他预览方式 -->
          <div v-else-if="previewUrl" class="preview-iframe-wrapper">
            <iframe 
              :src="previewUrl" 
              frameborder="0" 
              width="100%" 
              height="100%"
              class="document-preview-iframe"
            ></iframe>
          </div>
          
          <!-- 降级显示 -->
          <div v-else class="preview-fallback">
            <el-alert 
              title="无法加载预览" 
              type="warning" 
              :closable="false"
              style="margin-bottom: 20px"
            >
              文书预览暂时不可用，您可以查看文本内容或下载文档
            </el-alert>
            <div class="content-text">{{ currentDocument.content }}</div>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="viewVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleDownload">下载文书</el-button>
      </template>
    </el-dialog>

    <!-- 版本管理对话框 -->
    <el-dialog 
      v-model="versionVisible" 
      title="版本管理" 
      width="90%" 
      top="5vh"
      destroy-on-close
    >
      <VersionManager 
        v-if="currentDocument"
        :document-id="currentDocument.id"
        @refresh="handleVersionRefresh"
      />
    </el-dialog>

    <!-- 编辑文书对话框 -->
    <el-dialog 
      v-model="editVisible" 
      title="编辑文书" 
      width="90%" 
      top="5vh"
      destroy-on-close
      :close-on-click-modal="false"
    >
      <div v-if="editDocument" class="document-edit">
        <!-- 文书基本信息 -->
        <el-form :model="editDocument" label-width="100px" style="margin-bottom: 20px">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="文书标题">
                <el-input v-model="editDocument.title" placeholder="请输入文书标题" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="文书类型">
                <el-input v-model="editDocument.document_type" placeholder="文书类型" readonly />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="状态">
                <el-select v-model="editDocument.status" placeholder="请选择状态">
                  <el-option label="草稿" value="draft" />
                  <el-option label="已审核" value="reviewed" />
                  <el-option label="已定稿" value="finalized" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="密级">
                <el-select v-model="editDocument.classification" placeholder="请选择密级">
                  <el-option label="公开" value="public" />
                  <el-option label="内部" value="internal" />
                  <el-option label="秘密" value="confidential" />
                  <el-option label="机密" value="secret" />
                  <el-option label="绝密" value="top_secret" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>

        <!-- 富文本编辑器 -->
        <el-divider>文书内容</el-divider>
        <RichTextEditor v-model="editDocument.content" />
      </div>
      
      <template #footer>
        <el-button @click="handleCancelEdit">取消</el-button>
        <el-button type="primary" @click="handleSaveEdit" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 密级管理对话框 -->
    <el-dialog v-model="classificationVisible" title="更新密级" width="400px">
      <el-form label-width="80px">
        <el-form-item label="当前密级">
          <el-tag :color="getClassificationColor(classificationForm.classification)">
            {{ getClassificationText(classificationForm.classification) }}
          </el-tag>
        </el-form-item>
        <el-form-item label="新密级">
          <el-select v-model="classificationForm.newClassification" placeholder="请选择密级">
            <el-option label="公开" value="public" />
            <el-option label="内部" value="internal" />
            <el-option label="秘密" value="confidential" />
            <el-option label="机密" value="secret" />
            <el-option label="绝密" value="top_secret" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="classificationVisible = false">取消</el-button>
        <el-button type="primary" @click="handleClassificationUpdate">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 在线编辑对话框 -->
    <el-dialog 
      v-model="onlineEditVisible" 
      title="在线编辑文书" 
      width="90%" 
      top="5vh"
      destroy-on-close
      :close-on-click-modal="false"
    >
      <OnlyOfficeEditor
        v-if="currentDocument"
        :document-id="currentDocument.id"
        mode="edit"
        height="80vh"
        @error="handlePreviewError"
        @save="handleOnlineEditSave"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getDocumentList, updateClassification } from '@/api/documents'
import VersionManager from '@/components/VersionManager.vue'
import RichTextEditor from '@/components/RichTextEditor.vue'
import OnlyOfficeEditor from '@/components/OnlyOfficeEditor.vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'

const documentList = ref([])
const loading = ref(false)
const viewVisible = ref(false)
const versionVisible = ref(false)
const editVisible = ref(false)
const currentDocument = ref<any>(null)
const editDocument = ref<any>(null)
const saving = ref(false)
const previewUrl = ref('')
const previewLoading = ref(false)
const previewType = ref('')
const onlineEditVisible = ref(false)
const classificationVisible = ref(false)
const classificationForm = ref({
  documentId: 0,
  classification: 'public',
  newClassification: 'public'
})

const loadDocuments = async () => {
  loading.value = true
  try {
    const data: any = await getDocumentList()
    documentList.value = data
  } catch (error) {
    console.error(error)
    ElMessage.error('加载文书列表失败')
  } finally {
    loading.value = false
  }
}

const handleView = async (row: any) => {
  currentDocument.value = row
  previewUrl.value = ''
  previewType.value = ''
  previewLoading.value = true
  viewVisible.value = true
  
  try {
    // 如果文书已经有预览URL，直接使用
    if (row.preview_url) {
      if (row.preview_url === 'use_onlyoffice_component') {
        previewType.value = 'onlyoffice'
        console.log('[Documents] Using ONLYOFFICE component for preview')
      } else {
        previewUrl.value = row.preview_url
        previewType.value = 'direct'
        console.log('[Documents] Using direct URL for preview')
      }
      previewLoading.value = false
      return
    }
    
    // 否则，生成预览URL
    const response = await fetch(`http://localhost:8000/api/v1/documents/${row.id}/preview`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      if (data.preview_url) {
        if (data.preview_url === 'use_onlyoffice_component') {
          previewType.value = 'onlyoffice'
          console.log('[Documents] Fetched ONLYOFFICE preview')
        } else {
          previewUrl.value = data.preview_url
          previewType.value = 'direct'
          console.log('[Documents] Fetched preview URL:', data.preview_url)
        }
      }
    }
  } catch (error) {
    console.error('Failed to load preview:', error)
  } finally {
    previewLoading.value = false
  }
}

const handleDownload = async () => {
  if (!currentDocument.value) return
  
  try {
    const response = await fetch(`http://localhost:8000/api/v1/documents/${currentDocument.value.id}/export?format=docx`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (response.ok) {
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${currentDocument.value.title}.docx`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      ElMessage.success('文书下载成功')
    } else {
      throw new Error('下载失败')
    }
  } catch (error) {
    console.error('Download error:', error)
    ElMessage.error('文书下载失败')
  }
}

const handleEdit = (row: any) => {
  // 复制文书数据用于编辑
  editDocument.value = {
    id: row.id,
    title: row.title,
    content: row.content,
    document_type: row.document_type,
    status: row.status,
    classification: row.classification || 'public'
  }
  editVisible.value = true
}

const handleCancelEdit = () => {
  editVisible.value = false
  editDocument.value = null
}

const handleSaveEdit = async () => {
  if (!editDocument.value) return
  
  saving.value = true
  
  try {
    const response = await fetch(`/api/v1/documents/${editDocument.value.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        title: editDocument.value.title,
        content: editDocument.value.content,
        status: editDocument.value.status,
        classification: editDocument.value.classification,
        change_description: '手动编辑'
      })
    })
    
    if (response.ok) {
      ElMessage.success('文书保存成功')
      editVisible.value = false
      editDocument.value = null
      await loadDocuments()
    } else {
      const error = await response.json()
      throw new Error(error.detail || '保存失败')
    }
  } catch (error: any) {
    console.error('Save error:', error)
    ElMessage.error(error.message || '文书保存失败')
  } finally {
    saving.value = false
  }
}

const handleVersions = (row: any) => {
  currentDocument.value = row
  versionVisible.value = true
}

const handleVersionRefresh = () => {
  // 版本回滚后刷新文书列表
  loadDocuments()
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

const getStatusType = (status: string) => {
  const map: any = {
    draft: 'info',
    reviewed: 'success',
    finalized: 'warning'
  }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map: any = {
    draft: '草稿',
    reviewed: '已审核',
    finalized: '已定稿'
  }
  return map[status] || status
}

// 密级相关
const getClassificationText = (classification: string) => {
  const map: any = {
    public: '公开',
    internal: '内部',
    confidential: '秘密',
    secret: '机密',
    top_secret: '绝密'
  }
  return map[classification] || '公开'
}

const getClassificationColor = (classification: string) => {
  const map: any = {
    public: '#67C23A',
    internal: '#409EFF',
    confidential: '#E6A23C',
    secret: '#F56C6C',
    top_secret: '#909399'
  }
  return map[classification] || '#67C23A'
}

const handleClassification = (row: any) => {
  classificationForm.value = {
    documentId: row.id,
    classification: row.classification || 'public',
    newClassification: row.classification || 'public'
  }
  classificationVisible.value = true
}

const handleClassificationUpdate = async () => {
  try {
    await updateClassification(
      classificationForm.value.documentId,
      classificationForm.value.newClassification
    )
    ElMessage.success('密级更新成功')
    classificationVisible.value = false
    await loadDocuments()
  } catch (error) {
    console.error(error)
    ElMessage.error('密级更新失败')
  }
}

const handlePreviewError = (error: string) => {
  console.error('[Documents] Preview error:', error)
  ElMessage.error('预览加载失败')
}

const handleOnlineEdit = (row: any) => {
  currentDocument.value = row
  onlineEditVisible.value = true
}

const handleOnlineEditSave = () => {
  ElMessage.success('文书已保存')
  onlineEditVisible.value = false
  loadDocuments()
}

onMounted(() => {
  loadDocuments()
})
</script>

<style scoped>
.document-detail {
  padding: 10px;
}

.document-preview-container {
  width: 100%;
  height: 600px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
  background-color: #f5f7fa;
}

.preview-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}

.preview-loading .is-loading {
  animation: rotating 2s linear infinite;
  margin-bottom: 20px;
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.preview-iframe-wrapper {
  width: 100%;
  height: 100%;
}

.document-preview-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.preview-fallback {
  padding: 20px;
  height: 100%;
  overflow-y: auto;
}

.content-text {
  white-space: pre-wrap;
  line-height: 1.8;
  color: #666;
  background-color: white;
  padding: 20px;
  border-radius: 4px;
}

.document-edit {
  padding: 10px;
}

.document-edit :deep(.rich-text-editor) {
  margin-top: 10px;
}
</style>
