<template>
  <div class="files-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>文件管理</span>
          <div class="upload-buttons">
            <el-upload
              :before-upload="handleUpload"
              :show-file-list="false"
              accept=".pdf,.doc,.docx"
            >
              <el-button type="primary">上传文件</el-button>
            </el-upload>
            <el-upload
              :before-upload="() => false"
              :on-change="handleBatchSelect"
              :show-file-list="false"
              accept=".pdf,.doc,.docx"
              multiple
            >
              <el-button type="success">批量上传</el-button>
            </el-upload>
          </div>
        </div>
      </template>
      
      <!-- 批量上传进度 -->
      <el-alert
        v-if="batchUploading"
        title="批量上传中..."
        type="info"
        :closable="false"
        style="margin-bottom: 20px"
      >
        <el-progress
          :percentage="uploadProgress"
          :status="uploadProgress === 100 ? 'success' : undefined"
        />
        <p style="margin-top: 10px">
          已上传: {{ uploadedCount }} / {{ totalCount }} 个文件
        </p>
      </el-alert>
      
      <el-table :data="fileList" v-loading="loading">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="file_name" label="文件名" />
        <el-table-column prop="file_type" label="类型" width="100" />
        <el-table-column prop="file_size" label="大小" width="120">
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250">
          <template #default="{ row }">
            <el-button size="small" @click="handlePreview(row)">预览</el-button>
            <el-button size="small" type="primary" @click="handleReview(row)">研判</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog 
      v-model="previewVisible" 
      title="文件预览" 
      width="90%" 
      :fullscreen="true"
      class="preview-dialog"
    >
      <div class="preview-container">
        <!-- ONLYOFFICE预览 -->
        <OnlyOfficeEditor
          v-if="previewType === 'onlyoffice' && currentFile && !previewError"
          :file-id="currentFile.id"
          mode="view"
          height="calc(100vh - 120px)"
          @error="handlePreviewError"
        />
        
        <!-- 其他预览方式 -->
        <div v-else-if="previewUrl && !previewError" class="iframe-container">
          <iframe :src="previewUrl" @error="handlePreviewError" />
        </div>
        
        <!-- 错误提示 -->
        <div v-else class="preview-error">
          <el-empty description="无法预览该文件，可能是预览服务暂时不可用">
            <el-button type="primary" @click="handleDownloadCurrent">下载文件</el-button>
          </el-empty>
        </div>
      </div>
    </el-dialog>
    
    <!-- 批量上传结果对话框 -->
    <el-dialog v-model="batchResultVisible" title="批量上传结果" width="600px">
      <el-descriptions :column="3" border>
        <el-descriptions-item label="总数">{{ batchResult.total_count }}</el-descriptions-item>
        <el-descriptions-item label="成功">
          <el-tag type="success">{{ batchResult.success_count }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="失败">
          <el-tag type="danger">{{ batchResult.failed_count }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>
      
      <el-divider />
      
      <el-table :data="batchResult.results" max-height="400">
        <el-table-column prop="file_name" label="文件名" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.success ? 'success' : 'danger'">
              {{ row.success ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="error" label="错误信息" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { uploadFile, batchUploadFiles, getFileList, getFilePreview, deleteFile } from '@/api/files'
import { ElMessage, ElMessageBox } from 'element-plus'
import OnlyOfficeEditor from '@/components/OnlyOfficeEditor.vue'

const router = useRouter()
const fileList = ref([])
const loading = ref(false)
const previewVisible = ref(false)
const previewUrl = ref('')
const previewError = ref(false)
const previewType = ref('')
const currentFile = ref<any>(null)

// 批量上传相关
const batchUploading = ref(false)
const uploadProgress = ref(0)
const uploadedCount = ref(0)
const totalCount = ref(0)
const batchResultVisible = ref(false)
const batchResult = ref<any>({
  total_count: 0,
  success_count: 0,
  failed_count: 0,
  results: []
})

const loadFiles = async () => {
  loading.value = true
  try {
    const data: any = await getFileList()
    fileList.value = data
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleUpload = async (file: File) => {
  loading.value = true
  try {
    await uploadFile(file)
    ElMessage.success('文件上传成功')
    await loadFiles()
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
  return false
}

const handleBatchSelect = async (file: any, fileList: any[]) => {
  if (fileList.length === 0) return
  
  // 提取 File 对象
  const files = fileList.map(f => f.raw).filter(f => f)
  
  if (files.length === 0) {
    ElMessage.warning('请选择文件')
    return
  }
  
  // 开始批量上传
  batchUploading.value = true
  uploadProgress.value = 0
  uploadedCount.value = 0
  totalCount.value = files.length
  
  try {
    const result: any = await batchUploadFiles(files)
    
    uploadProgress.value = 100
    uploadedCount.value = result.success_count
    batchResult.value = result
    
    if (result.success_count > 0) {
      ElMessage.success(`成功上传 ${result.success_count} 个文件`)
      await loadFiles()
    }
    
    if (result.failed_count > 0) {
      ElMessage.warning(`${result.failed_count} 个文件上传失败`)
      batchResultVisible.value = true
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('批量上传失败')
  } finally {
    setTimeout(() => {
      batchUploading.value = false
    }, 1000)
  }
}

const handlePreview = async (row: any) => {
  try {
    // 防御性检查：确保row和row.id存在
    if (!row || !row.id) {
      ElMessage.error('文件ID无效')
      console.error('Invalid file row:', row)
      return
    }
    
    console.log('[Files] ========== Preview Request ==========')
    console.log('[Files] File:', row)
    
    currentFile.value = row
    previewError.value = false
    previewType.value = ''
    
    console.log('[Files] Calling getFilePreview...')
    const data: any = await getFilePreview(row.id)
    
    console.log('[Files] Preview data received:', data)
    console.log('[Files] preview_url:', data.preview_url)
    console.log('[Files] preview_type:', data.preview_type)
    
    if (!data.preview_url) {
      console.error('[Files] No preview_url in response')
      previewError.value = true
      ElMessage.warning('预览服务暂时不可用')
    } else {
      // 检查是否是ONLYOFFICE预览
      if (data.preview_url === 'use_onlyoffice_component') {
        previewType.value = 'onlyoffice'
        console.log('[Files] ✅ Setting previewType to "onlyoffice"')
        console.log('[Files] currentFile:', currentFile.value)
        console.log('[Files] previewError:', previewError.value)
      } else {
        previewUrl.value = data.preview_url
        previewType.value = 'direct'
        console.log('[Files] Using direct URL for preview:', data.preview_url)
      }
    }
    
    console.log('[Files] Opening preview dialog...')
    console.log('[Files] previewType:', previewType.value)
    console.log('[Files] previewVisible will be set to true')
    previewVisible.value = true
    
    // 延迟检查 DOM
    setTimeout(() => {
      const editorElement = document.getElementById('onlyoffice-editor')
      const loadingElement = document.querySelector('.onlyoffice-editor .loading')
      console.log('[Files] DOM Check:')
      console.log('  - onlyoffice-editor element:', editorElement)
      console.log('  - loading element:', loadingElement)
      console.log('  - previewType:', previewType.value)
    }, 100)
  } catch (error) {
    console.error('[Files] Preview error:', error)
    previewError.value = true
    previewVisible.value = true
  }
}

const handlePreviewError = () => {
  previewError.value = true
}

const handleDownloadCurrent = () => {
  if (currentFile.value) {
    // 触发文件下载
    window.open(`/api/v1/files/${currentFile.value.id}/download`, '_blank')
  }
}

const handleReview = (row: any) => {
  // 防御性检查：确保row和row.id存在
  if (!row || !row.id) {
    ElMessage.error('文件ID无效')
    console.error('Invalid file row:', row)
    return
  }
  
  router.push(`/review/${row.id}`)
}

const handleDelete = async (row: any) => {
  try {
    // 防御性检查：确保row和row.id存在
    if (!row || !row.id) {
      ElMessage.error('文件ID无效')
      console.error('Invalid file row:', row)
      return
    }
    
    await ElMessageBox.confirm('确定要删除该文件吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await deleteFile(row.id)
    ElMessage.success('删除成功')
    await loadFiles()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}

const formatFileSize = (size: number) => {
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(2) + ' KB'
  return (size / (1024 * 1024)).toFixed(2) + ' MB'
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

const getStatusType = (status: string) => {
  const map: any = {
    uploaded: 'info',
    reviewed: 'success',
    generated: 'warning'
  }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map: any = {
    uploaded: '已上传',
    reviewed: '已研判',
    generated: '已生成'
  }
  return map[status] || status
}

onMounted(() => {
  loadFiles()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-buttons {
  display: flex;
  gap: 10px;
}

.preview-container {
  width: 100%;
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
}

.iframe-container {
  width: 100%;
  height: 100%;
}

.iframe-container iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.preview-error {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

/* 优化预览对话框样式 */
:deep(.preview-dialog .el-dialog__body) {
  padding: 0 !important;
  height: calc(100vh - 60px);
}

:deep(.preview-dialog .el-dialog__header) {
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
}
</style>
