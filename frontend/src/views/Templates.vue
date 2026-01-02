<template>
  <div class="templates-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>模板管理</span>
          <div>
            <el-button type="success" @click="extractDialogVisible = true">
              <el-icon><Upload /></el-icon>
              从文件提取
            </el-button>
            <el-button type="primary" @click="createDialogVisible = true">
              <el-icon><Plus /></el-icon>
              创建模板
            </el-button>
          </div>
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
    
    <!-- 创建模板对话框 -->
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

    <!-- 模板提取对话框 -->
    <el-dialog v-model="extractDialogVisible" title="从文件提取模板" width="800px">
      <el-steps :active="extractStep" finish-status="success" align-center style="margin-bottom: 20px">
        <el-step title="选择文件" />
        <el-step title="AI 提取" />
        <el-step title="确认保存" />
      </el-steps>

      <!-- 步骤 1: 选择文件 -->
      <div v-if="extractStep === 0">
        <el-alert 
          title="提示" 
          type="info" 
          :closable="false"
          style="margin-bottom: 20px"
        >
          请选择一个已上传的文件作为模板来源，系统将自动分析文件结构并提取模板
        </el-alert>
        
        <el-table 
          :data="fileList" 
          v-loading="fileLoading"
          @row-click="handleSelectFile"
          highlight-current-row
          style="cursor: pointer"
        >
          <el-table-column type="index" label="序号" width="60" />
          <el-table-column prop="filename" label="文件名" />
          <el-table-column prop="file_type" label="类型" width="100">
            <template #default="{ row }">
              <el-tag size="small">{{ row.file_type.toUpperCase() }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="上传时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 步骤 2: AI 提取中 -->
      <div v-if="extractStep === 1" style="text-align: center; padding: 40px 0">
        <el-icon :size="60" class="is-loading" color="#409EFF">
          <Loading />
        </el-icon>
        <p style="margin-top: 20px; font-size: 16px">AI 正在分析文件结构...</p>
        <p style="color: #909399">这可能需要几秒钟，请稍候</p>
      </div>

      <!-- 步骤 3: 确认提取结果 -->
      <div v-if="extractStep === 2">
        <el-alert 
          title="提取成功" 
          type="success" 
          :closable="false"
          style="margin-bottom: 20px"
        >
          AI 已成功提取模板结构，请确认信息后保存
        </el-alert>

        <el-form :model="extractedTemplate" label-width="100px">
          <el-form-item label="模板名称">
            <el-input v-model="extractedTemplate.name" placeholder="请输入模板名称" />
          </el-form-item>
          <el-form-item label="文书类型">
            <el-input v-model="extractedTemplate.document_type" placeholder="AI 识别的文书类型" />
          </el-form-item>
          <el-form-item label="字段列表">
            <el-tag 
              v-for="(field, index) in extractedTemplate.fields" 
              :key="index"
              style="margin-right: 10px; margin-bottom: 10px"
            >
              {{ field.name }} ({{ field.type }})
            </el-tag>
          </el-form-item>
          <el-form-item label="结构描述">
            <el-input 
              v-model="extractedTemplate.structure_text" 
              type="textarea" 
              :rows="4" 
              readonly
            />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <div v-if="extractStep === 0">
          <el-button @click="extractDialogVisible = false">取消</el-button>
        </div>
        <div v-if="extractStep === 2">
          <el-button @click="handleCancelExtract">取消</el-button>
          <el-button type="primary" @click="handleSaveExtracted">保存模板</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Upload, Loading } from '@element-plus/icons-vue'
import { getTemplateList, createTemplate, extractTemplate, saveExtractedTemplate } from '@/api/templates'
import { getFileList } from '@/api/files'
import { ElMessage } from 'element-plus'

const router = useRouter()
const templateList = ref<any[]>([])
const loading = ref(false)
const createDialogVisible = ref(false)

const form = ref({
  name: '',
  document_type: '',
  content_template: '',
  structure: {},
  fields: {}
})

// 模板提取相关
const extractDialogVisible = ref(false)
const extractStep = ref(0) // 0: 选择文件, 1: AI 提取中, 2: 确认保存
const fileList = ref<any[]>([])
const fileLoading = ref(false)
const selectedFile = ref<any>(null)
const extractedTemplate = ref<any>({
  name: '',
  document_type: '',
  structure: {},
  structure_text: '',
  content_template: '',
  fields: []
})

const loadTemplates = async () => {
  loading.value = true
  try {
    const data: any = await getTemplateList()
    templateList.value = data
  } catch (error) {
    console.error(error)
    ElMessage.error('加载模板列表失败')
  } finally {
    loading.value = false
  }
}

const loadFiles = async () => {
  fileLoading.value = true
  try {
    const data: any = await getFileList()
    fileList.value = data.items || []
  } catch (error) {
    console.error(error)
    ElMessage.error('加载文件列表失败')
  } finally {
    fileLoading.value = false
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
    ElMessage.error('模板创建失败')
  }
}

const handleView = (row: any) => {
  console.log('View:', row)
}

const handleUse = (row: any) => {
  router.push({ path: '/generate', query: { templateId: row.id } })
}

// 模板提取流程
const handleSelectFile = async (row: any) => {
  selectedFile.value = row
  extractStep.value = 1
  
  try {
    // 调用 AI 提取接口
    const result: any = await extractTemplate(row.id, false)
    
    if (result.success) {
      const templateData = result.template_data
      
      // 填充提取结果
      extractedTemplate.value = {
        name: `${row.filename} - 提取模板`,
        document_type: templateData.document_type || '未知类型',
        structure: templateData.structure || {},
        structure_text: JSON.stringify(templateData.structure || {}, null, 2),
        content_template: templateData.fixed_parts || '',
        fields: Array.isArray(templateData.fields) ? templateData.fields : []
      }
      
      extractStep.value = 2
      ElMessage.success('模板提取成功')
    } else {
      throw new Error(result.message || '提取失败')
    }
  } catch (error: any) {
    console.error(error)
    ElMessage.error(error.response?.data?.detail || '模板提取失败')
    extractStep.value = 0
  }
}

const handleSaveExtracted = async () => {
  try {
    const data = {
      name: extractedTemplate.value.name,
      document_type: extractedTemplate.value.document_type,
      structure: extractedTemplate.value.structure,
      content_template: extractedTemplate.value.content_template,
      fields: extractedTemplate.value.fields.reduce((acc: any, field: any) => {
        acc[field.id] = field
        return acc
      }, {})
    }
    
    await saveExtractedTemplate(data)
    ElMessage.success('模板保存成功')
    extractDialogVisible.value = false
    extractStep.value = 0
    await loadTemplates()
  } catch (error) {
    console.error(error)
    ElMessage.error('模板保存失败')
  }
}

const handleCancelExtract = () => {
  extractDialogVisible.value = false
  extractStep.value = 0
  selectedFile.value = null
  extractedTemplate.value = {
    name: '',
    document_type: '',
    structure: {},
    structure_text: '',
    content_template: '',
    fields: []
  }
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

// 监听提取对话框打开
const handleExtractDialogOpen = () => {
  extractStep.value = 0
  loadFiles()
}

// 监听对话框打开
onMounted(() => {
  loadTemplates()
})

// 监听 extractDialogVisible 变化
import { watch } from 'vue'
watch(extractDialogVisible, (newVal) => {
  if (newVal) {
    handleExtractDialogOpen()
  }
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.is-loading {
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
