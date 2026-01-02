<template>
  <div class="templates-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>模板管理</span>
          <el-button type="primary" @click="createDialogVisible = true">创建模板</el-button>
        </div>
      </template>
      
      <el-table :data="templateList" v-loading="loading">
        <el-table-column prop="name" label="模板名称" />
        <el-table-column prop="document_type" label="文书类型" width="150" />
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="handleView(row)">查看</el-button>
            <el-button size="small" type="primary" @click="handleUse(row)">使用</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog v-model="createDialogVisible" title="创建模板" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="模板名称">
          <el-input v-model="form.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="文书类型">
          <el-select v-model="form.document_type" placeholder="请选择文书类型">
            <el-option label="受理通知书" value="acceptance_notice" />
            <el-option label="转办函" value="transfer_letter" />
            <el-option label="答复意见书" value="reply_letter" />
            <el-option label="不予受理通知书" value="rejection_notice" />
          </el-select>
        </el-form-item>
        <el-form-item label="模板内容">
          <el-input v-model="form.content_template" type="textarea" :rows="10" placeholder="请输入模板内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getTemplateList, createTemplate } from '@/api/templates'
import { ElMessage } from 'element-plus'

const router = useRouter()
const templateList = ref([])
const loading = ref(false)
const createDialogVisible = ref(false)

const form = ref({
  name: '',
  document_type: '',
  content_template: '',
  structure: {},
  fields: {}
})

const loadTemplates = async () => {
  loading.value = true
  try {
    templateList.value = await getTemplateList()
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleCreate = async () => {
  try {
    await createTemplate(form.value)
    ElMessage.success('模板创建成功')
    createDialogVisible.value = false
    await loadTemplates()
  } catch (error) {
    console.error(error)
  }
}

const handleView = (row: any) => {
  console.log('View:', row)
}

const handleUse = (row: any) => {
  router.push({ path: '/generate', query: { templateId: row.id } })
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

onMounted(() => {
  loadTemplates()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
