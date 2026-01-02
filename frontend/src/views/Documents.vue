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
        <el-table-column label="操作" width="280">
          <template #default="{ row }">
            <el-button-group>
              <el-button size="small" @click="handleView(row)">查看</el-button>
              <el-button size="small" type="primary" @click="handleEdit(row)">编辑</el-button>
              <el-button size="small" type="info" @click="handleVersions(row)">版本</el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 文书详情对话框 -->
    <el-dialog v-model="viewVisible" title="文书详情" width="80%">
      <div v-if="currentDocument" class="document-content">
        <h3>{{ currentDocument.title }}</h3>
        <div class="content-text">{{ currentDocument.content }}</div>
      </div>
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getDocumentList, updateClassification } from '@/api/documents'
import VersionManager from '@/components/VersionManager.vue'
import { ElMessage } from 'element-plus'

const documentList = ref([])
const loading = ref(false)
const viewVisible = ref(false)
const versionVisible = ref(false)
const currentDocument = ref<any>(null)
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

const handleView = (row: any) => {
  currentDocument.value = row
  viewVisible.value = true
}

const handleEdit = (row: any) => {
  // TODO: 实现编辑功能
  ElMessage.info('编辑功能开发中')
  console.log('Edit:', row)
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
