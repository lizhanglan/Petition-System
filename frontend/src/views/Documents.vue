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
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="handleView(row)">查看</el-button>
            <el-button size="small" type="primary" @click="handleEdit(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog v-model="viewVisible" title="文书详情" width="80%">
      <div v-if="currentDocument" class="document-content">
        <h3>{{ currentDocument.title }}</h3>
        <div class="content-text">{{ currentDocument.content }}</div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getDocumentList } from '@/api/documents'

const documentList = ref([])
const loading = ref(false)
const viewVisible = ref(false)
const currentDocument = ref<any>(null)

const loadDocuments = async () => {
  loading.value = true
  try {
    documentList.value = await getDocumentList()
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleView = (row: any) => {
  currentDocument.value = row
  viewVisible.value = true
}

const handleEdit = (row: any) => {
  // TODO: 实现编辑功能
  console.log('Edit:', row)
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

onMounted(() => {
  loadDocuments()
})
</script>

<style scoped>
.document-content {
  padding: 20px;
}

.document-content h3 {
  margin-bottom: 20px;
  color: #333;
}

.content-text {
  white-space: pre-wrap;
  line-height: 1.8;
  color: #666;
}
</style>
