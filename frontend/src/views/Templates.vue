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

    <!-- 查看模板对话框 -->
    <el-dialog v-model="viewDialogVisible" title="查看模板详情" width="800px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="模板名称">
          {{ viewTemplate.name }}
        </el-descriptions-item>
        <el-descriptions-item label="文书类型">
          {{ viewTemplate.document_type }}
        </el-descriptions-item>
        <el-descriptions-item label="版本">
          {{ viewTemplate.version }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="viewTemplate.is_active ? 'success' : 'info'">
            {{ viewTemplate.is_active ? '启用' : '停用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDate(viewTemplate.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间">
          {{ formatDate(viewTemplate.updated_at) }}
        </el-descriptions-item>
      </el-descriptions>

      <el-divider>模板结构</el-divider>
      <el-input 
        v-model="viewTemplateStructure" 
        type="textarea" 
        :rows="6" 
        readonly
        placeholder="暂无结构信息"
      />

      <el-divider>字段列表</el-divider>
      <el-table :data="viewTemplateFields" border>
        <el-table-column prop="name" label="字段名称" />
        <el-table-column prop="type" label="字段类型" width="120" />
        <el-table-column prop="required" label="是否必填" width="100">
          <template #default="{ row }">
            <el-tag :type="row.required ? 'danger' : 'info'" size="small">
              {{ row.required ? '必填' : '可选' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="default_value" label="默认值" />
      </el-table>

      <el-divider>模板内容</el-divider>
      <el-input 
        v-model="viewTemplate.content_template" 
        type="textarea" 
        :rows="10" 
        readonly
        placeholder="暂无模板内容"
      />

      <template #footer>
        <el-button @click="viewDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleUseFromView">使用此模板</el-button>
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
          请选择文件来源：从已上传的文件中选择，或从本地上传新文件
        </el-alert>

        <!-- 文件来源选择 -->
        <el-radio-group v-model="fileSource" style="margin-bottom: 20px">
          <el-radio-button value="uploaded">从已上传文件选择</el-radio-button>
          <el-radio-button value="local">从本地上传</el-radio-button>
        </el-radio-group>

        <!-- 从已上传文件选择 -->
        <div v-if="fileSource === 'uploaded'">
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
          
          <el-empty 
            v-if="!fileLoading && fileList.length === 0" 
            description="暂无已上传的文件，请先上传文件或选择从本地上传"
          />
        </div>

        <!-- 从本地上传 -->
        <div v-if="fileSource === 'local'" style="text-align: center; padding: 40px 0">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-exceed="handleExceed"
            accept=".pdf,.doc,.docx"
            drag
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 PDF、Word 格式，文件大小不超过 10MB
              </div>
            </template>
          </el-upload>

          <el-button 
            v-if="localFile" 
            type="primary" 
            style="margin-top: 20px"
            @click="handleUploadAndExtract"
            :loading="uploading"
          >
            上传并提取模板
          </el-button>
        </div>
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
import { Plus, Upload, Loading, UploadFilled } from '@element-plus/icons-vue'
import { getTemplateList, createTemplate, extractTemplate, saveExtractedTemplate } from '@/api/templates'
import { getFileList, uploadFile } from '@/api/files'
import { ElMessage } from 'element-plus'
import type { UploadInstance, UploadProps, UploadRawFile } from 'element-plus'

const router = useRouter()
const templateList = ref<any[]>([])
const loading = ref(false)
const createDialogVisible = ref(false)
const viewDialogVisible = ref(false)
const viewTemplate = ref<any>({})
const viewTemplateStructure = ref('')
const viewTemplateFields = ref<any[]>([])

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
const fileSource = ref('uploaded') // 'uploaded' 或 'local'
const fileList = ref<any[]>([])
const fileLoading = ref(false)
const selectedFile = ref<any>(null)
const localFile = ref<File | null>(null)
const uploadRef = ref<UploadInstance>()
const uploading = ref(false)
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
  viewTemplate.value = { ...row }
  
  // 处理结构信息
  if (row.structure) {
    if (typeof row.structure === 'string') {
      viewTemplateStructure.value = row.structure
    } else {
      viewTemplateStructure.value = JSON.stringify(row.structure, null, 2)
    }
  } else {
    viewTemplateStructure.value = ''
  }
  
  // 处理字段列表
  if (row.fields) {
    if (typeof row.fields === 'object' && !Array.isArray(row.fields)) {
      // 如果是对象，转换为数组
      viewTemplateFields.value = Object.entries(row.fields).map(([key, value]: [string, any]) => ({
        name: value.name || key,
        type: value.type || 'text',
        required: value.required || false,
        default_value: value.default_value || ''
      }))
    } else if (Array.isArray(row.fields)) {
      viewTemplateFields.value = row.fields
    } else {
      viewTemplateFields.value = []
    }
  } else {
    viewTemplateFields.value = []
  }
  
  viewDialogVisible.value = true
}

const handleUse = (row: any) => {
  router.push({ path: '/generate', query: { templateId: row.id } })
}

const handleUseFromView = () => {
  viewDialogVisible.value = false
  router.push({ path: '/generate', query: { templateId: viewTemplate.value.id } })
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
        name: `${row.file_name} - 提取模板`,
        document_type: templateData.document_type || '未知类型',
        structure: templateData.structure || {},
        structure_text: JSON.stringify(templateData.structure || {}, null, 2),
        content_template: templateData.fixed_parts || templateData.content_template || '',
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
    // 处理fields：如果是数组，转换为对象；如果已经是对象，直接使用
    let fieldsObj = {}
    if (Array.isArray(extractedTemplate.value.fields)) {
      extractedTemplate.value.fields.forEach((field: any, index: number) => {
        const fieldId = field.id || field.name || `field_${index}`
        fieldsObj[fieldId] = {
          name: field.name || '',
          type: field.type || 'text',
          required: field.required || false,
          default_value: field.default_value || ''
        }
      })
    } else if (typeof extractedTemplate.value.fields === 'object') {
      fieldsObj = extractedTemplate.value.fields
    }
    
    // 确保structure是对象（dict）
    let structure = extractedTemplate.value.structure
    if (typeof structure === 'string') {
      // 如果是字符串，尝试解析为对象，如果失败则包装为对象
      try {
        structure = JSON.parse(structure)
      } catch {
        structure = { description: structure }
      }
    } else if (!structure || typeof structure !== 'object') {
      structure = {}
    }
    
    // 确保content_template是字符串
    let contentTemplate = extractedTemplate.value.content_template
    if (typeof contentTemplate === 'object' && contentTemplate !== null) {
      // 如果是对象，转换为JSON字符串
      contentTemplate = JSON.stringify(contentTemplate, null, 2)
    } else if (!contentTemplate) {
      contentTemplate = ''
    } else {
      contentTemplate = String(contentTemplate)
    }
    
    const data = {
      name: extractedTemplate.value.name,
      document_type: extractedTemplate.value.document_type,
      structure: structure,
      content_template: contentTemplate,
      fields: fieldsObj
    }
    
    console.log('Saving template data:', JSON.stringify(data, null, 2))
    
    await saveExtractedTemplate(data)
    ElMessage.success('模板保存成功')
    extractDialogVisible.value = false
    extractStep.value = 0
    await loadTemplates()
  } catch (error: any) {
    console.error('Save template error:', error)
    console.error('Error response:', error.response?.data)
    if (error.response?.data?.detail) {
      console.error('Validation errors:', JSON.stringify(error.response.data.detail, null, 2))
    }
    const errorMsg = error.response?.data?.detail?.[0]?.msg || error.response?.data?.detail || '模板保存失败'
    ElMessage.error(errorMsg)
  }
}

const handleCancelExtract = () => {
  extractDialogVisible.value = false
  extractStep.value = 0
  fileSource.value = 'uploaded'
  selectedFile.value = null
  localFile.value = null
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
  extractedTemplate.value = {
    name: '',
    document_type: '',
    structure: {},
    structure_text: '',
    content_template: '',
    fields: []
  }
}

// 处理本地文件选择
const handleFileChange: UploadProps['onChange'] = (uploadFile) => {
  localFile.value = uploadFile.raw as File
}

const handleExceed: UploadProps['onExceed'] = (files) => {
  uploadRef.value!.clearFiles()
  const file = files[0] as UploadRawFile
  uploadRef.value!.handleStart(file)
  localFile.value = file
}

// 上传并提取模板
const handleUploadAndExtract = async () => {
  if (!localFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  uploading.value = true
  
  try {
    // 1. 先上传文件
    const uploadResult: any = await uploadFile(localFile.value)
    
    if (!uploadResult || !uploadResult.id) {
      throw new Error('文件上传失败')
    }

    ElMessage.success('文件上传成功，开始提取模板...')
    
    // 2. 使用上传的文件ID进行模板提取
    extractStep.value = 1
    
    const result: any = await extractTemplate(uploadResult.id, false)
    
    if (result.success) {
      const templateData = result.template_data
      
      // 填充提取结果
      extractedTemplate.value = {
        name: `${localFile.value.name} - 提取模板`,
        document_type: templateData.document_type || '未知类型',
        structure: templateData.structure || {},
        structure_text: JSON.stringify(templateData.structure || {}, null, 2),
        content_template: templateData.fixed_parts || templateData.content_template || '',
        fields: Array.isArray(templateData.fields) ? templateData.fields : []
      }
      
      extractStep.value = 2
      ElMessage.success('模板提取成功')
    } else {
      throw new Error(result.message || '提取失败')
    }
  } catch (error: any) {
    console.error(error)
    ElMessage.error(error.response?.data?.detail || error.message || '上传或提取失败')
    extractStep.value = 0
  } finally {
    uploading.value = false
  }
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

// 监听提取对话框打开
const handleExtractDialogOpen = () => {
  extractStep.value = 0
  fileSource.value = 'uploaded'
  localFile.value = null
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
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
