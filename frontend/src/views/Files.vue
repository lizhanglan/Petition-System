<template>
  <div class="files-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>文件管理</span>
          <el-upload
            :before-upload="handleUpload"
            :show-file-list="false"
            accept=".pdf,.doc,.docx"
          >
            <el-button type="primary">上传文件</el-button>
          </el-upload>
        </div>
      </template>
      
      <el-table :data="fileList" v-loading="loading">
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
    
    <el-dialog v-model="previewVisible" title="文件预览" width="80%" :fullscreen="true">
      <div v-if="previewUrl && !previewError">
        <iframe :src="previewUrl" style="width: 100%; height: 80vh; border: none;" @error="handlePreviewError" />
      </div>
      <div v-else class="preview-error">
        <el-empty description="无法预览该文件，可能是预览服务暂时不可用">
          <el-button type="primary" @click="handleDownloadCurrent">下载文件</el-button>
        </el-empty>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { uploadFile, getFileList, getFilePreview, deleteFile } from '@/api/files'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const fileList = ref([])
const loading = ref(false)
const previewVisible = ref(false)
const previewUrl = ref('')
const previewError = ref(false)
const currentFile = ref<any>(null)

const loadFiles = async () => {
  loading.value = true
  try {
    fileList.value = await getFileList()
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

const handlePreview = async (row: any) => {
  try {
    currentFile.value = row
    previewError.value = false
    const data = await getFilePreview(row.id)
    
    if (!data.preview_url) {
      previewError.value = true
      ElMessage.warning('预览服务暂时不可用')
    } else {
      previewUrl.value = data.preview_url
    }
    
    previewVisible.value = true
  } catch (error) {
    console.error(error)
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
  router.push(`/review/${row.id}`)
}

const handleDelete = async (row: any) => {
  try {
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

.preview-error {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 80vh;
}
</style>
