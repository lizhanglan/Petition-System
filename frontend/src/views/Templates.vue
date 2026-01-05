<template>
  <div class="templates-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>模板管理</span>
          <el-button type="primary" @click="uploadDialogVisible = true">
            <el-icon><Upload /></el-icon>
            上传 Word 模板
          </el-button>
        </div>
      </template>
      
      <el-table :data="templateList" v-loading="loading">
        <el-table-column prop="name" label="模板名称" />
        <el-table-column prop="document_type" label="文书类型" width="150" />
        <el-table-column label="字段数" width="100">
          <template #default="{ row }">
            {{ row.fields ? Object.keys(row.fields).length : 0 }}
          </template>
        </el-table-column>
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
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="handleView(row)">查看</el-button>
            <el-button size="small" type="primary" @click="handleUse(row)">使用</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-empty v-if="!loading && templateList.length === 0" description="暂无模板，请上传 Word 模板" />
    </el-card>
    
    <!-- 上传模板对话框 -->
    <el-dialog 
      v-model="uploadDialogVisible" 
      :title="uploadStep === 2 ? '确认模板信息' : '上传 Word 模板'"
      :width="uploadStep === 2 ? '90%' : '700px'"
      :fullscreen="uploadStep === 2"
      destroy-on-close
    >
      <el-steps :active="uploadStep" finish-status="success" align-center style="margin-bottom: 30px">
        <el-step title="上传文件" />
        <el-step title="AI 处理" />
        <el-step title="确认保存" />
      </el-steps>

      <!-- 步骤 1: 上传文件 -->
      <div v-if="uploadStep === 0" class="upload-step">
        <!-- 上传提示 -->
        <el-alert 
          title="上传须知" 
          type="warning" 
          :closable="false"
          style="margin-bottom: 20px"
        >
          <template #default>
            <p style="margin: 0 0 8px 0">请上传<strong>纯净的文书模板</strong>，上传前请确保已移除以下内容：</p>
            <ul style="margin: 0; padding-left: 20px; color: #909399">
              <li>公章、印章图片</li>
              <li>手写签名或签名图片</li>
              <li>附件清单及附件内容</li>
              <li>批注、修订痕迹</li>
              <li>页眉页脚中的敏感信息（如具体人员信息）</li>
            </ul>
            <p style="margin: 8px 0 0 0; color: #409eff">
              <el-icon><InfoFilled /></el-icon>
              AI 将自动识别可变字段（如姓名、日期、编号等）并替换为占位符
            </p>
          </template>
        </el-alert>

        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :limit="1"
          :on-change="handleFileChange"
          :on-exceed="handleExceed"
          accept=".docx,.doc"
          drag
          class="template-upload"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将 Word 文档拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              仅支持 .docx 格式，建议文件大小不超过 5MB
            </div>
          </template>
        </el-upload>

        <div v-if="selectedFile" style="margin-top: 20px; text-align: center">
          <el-button type="primary" @click="handleUpload" :loading="uploading" size="large">
            <el-icon><Upload /></el-icon>
            上传并处理
          </el-button>
        </div>
      </div>

      <!-- 步骤 2: AI 处理中 -->
      <div v-if="uploadStep === 1" class="processing-step">
        <el-icon :size="60" class="is-loading" color="#409EFF">
          <Loading />
        </el-icon>
        <p class="processing-title">AI 正在分析文档并识别可变字段...</p>
        <p class="processing-hint">这可能需要 10-30 秒，请稍候</p>
      </div>

      <!-- 步骤 3: 确认保存 - 左右分栏 -->
      <div v-if="uploadStep === 2" class="confirm-step">
        <div class="confirm-layout">
          <!-- 左侧：模板预览 -->
          <div class="preview-panel">
            <div class="panel-header">
              <el-icon><Document /></el-icon>
              <span>模板预览</span>
            </div>
            <div class="preview-content">
              <DocxPreview 
                v-if="previewBlob"
                :blob="previewBlob"
                @loaded="handlePreviewLoaded"
                @error="handlePreviewError"
              />
              <el-empty v-else description="加载预览中..." />
            </div>
          </div>

          <!-- 右侧：字段信息和表单 -->
          <div class="info-panel">
            <div class="panel-header">
              <el-icon><Setting /></el-icon>
              <span>模板信息</span>
            </div>
            <div class="info-content">
              <el-form :model="confirmForm" label-width="100px">
                <el-form-item label="模板名称" required>
                  <el-input v-model="confirmForm.name" placeholder="请输入模板名称" />
                </el-form-item>
                <el-form-item label="文书类型" required>
                  <el-select v-model="confirmForm.document_type" placeholder="请选择文书类型" style="width: 100%">
                    <el-option label="受理通知书" value="acceptance_notice" />
                    <el-option label="转办函" value="transfer_letter" />
                    <el-option label="答复意见书" value="reply_letter" />
                    <el-option label="不予受理通知书" value="rejection_notice" />
                    <el-option label="其他" value="other" />
                  </el-select>
                </el-form-item>
              </el-form>

              <el-divider>
                <el-icon><List /></el-icon>
                识别的字段 ({{ fieldsList.length }})
              </el-divider>
              
              <el-table :data="fieldsList" border size="small" max-height="300">
                <el-table-column prop="name" label="变量名" width="140" />
                <el-table-column prop="label" label="中文名称" />
                <el-table-column prop="type" label="类型" width="80">
                  <template #default="{ row }">
                    <el-tag size="small">{{ getTypeLabel(row.type) }}</el-tag>
                  </template>
                </el-table-column>
              </el-table>

              <el-divider v-if="replacementsList.length > 0">
                <el-icon><Switch /></el-icon>
                替换映射
              </el-divider>
              
              <el-table v-if="replacementsList.length > 0" :data="replacementsList" border size="small" max-height="200">
                <el-table-column prop="original" label="原文内容" />
                <el-table-column prop="placeholder" label="占位符" width="180">
                  <template #default="{ row }">
                    <code>{{ row.placeholder }}</code>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div v-if="uploadStep === 0">
          <el-button @click="handleCancelUpload">取消</el-button>
        </div>
        <div v-if="uploadStep === 2" class="confirm-footer">
          <el-button @click="handleReupload">
            <el-icon><RefreshLeft /></el-icon>
            重新上传
          </el-button>
          <el-button type="primary" @click="handleConfirmSave" :loading="saving">
            <el-icon><Check /></el-icon>
            保存模板
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 查看模板对话框 -->
    <el-dialog v-model="viewDialogVisible" title="模板详情" width="800px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="模板名称">{{ viewTemplate.name }}</el-descriptions-item>
        <el-descriptions-item label="文书类型">{{ viewTemplate.document_type }}</el-descriptions-item>
        <el-descriptions-item label="版本">{{ viewTemplate.version }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="viewTemplate.is_active ? 'success' : 'info'">
            {{ viewTemplate.is_active ? '启用' : '停用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间" :span="2">
          {{ formatDate(viewTemplate.created_at) }}
        </el-descriptions-item>
      </el-descriptions>

      <el-divider>字段列表</el-divider>
      
      <TemplatePreview :fields="viewTemplate.fields || {}" />

      <template #footer>
        <el-button @click="viewDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleUseFromView">使用此模板</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Upload, Loading, UploadFilled, Document, Setting, 
  List, Switch, RefreshLeft, Check, InfoFilled 
} from '@element-plus/icons-vue'
import { 
  getTemplateList, 
  uploadAndProcessTemplate, 
  confirmTemplate,
  deleteTemplate
} from '@/api/templates'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { UploadInstance, UploadProps, UploadRawFile } from 'element-plus'
import TemplatePreview from '@/components/TemplatePreview.vue'
import DocxPreview from '@/components/DocxPreview.vue'

const router = useRouter()
const templateList = ref<any[]>([])
const loading = ref(false)

// 上传对话框
const uploadDialogVisible = ref(false)
const uploadStep = ref(0) // 0: 上传, 1: AI处理, 2: 确认
const uploadRef = ref<UploadInstance>()
const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const saving = ref(false)
const previewData = ref<any>({})
const previewBlob = ref<Blob | null>(null)
const confirmForm = ref({
  name: '',
  document_type: ''
})

// 查看对话框
const viewDialogVisible = ref(false)
const viewTemplate = ref<any>({})

// 计算字段列表
const fieldsList = computed(() => {
  if (!previewData.value.fields) return []
  return Object.entries(previewData.value.fields).map(([name, info]: [string, any]) => ({
    name,
    label: info.label || name,
    type: info.type || 'text',
    required: info.required || false
  }))
})

// 计算替换列表
const replacementsList = computed(() => {
  if (!previewData.value.replacements) return []
  return Object.entries(previewData.value.replacements).map(([original, placeholder]) => ({
    original,
    placeholder
  }))
})

const loadTemplates = async () => {
  loading.value = true
  try {
    const data: any = await getTemplateList()
    templateList.value = data || []
  } catch (error) {
    console.error(error)
    ElMessage.error('加载模板列表失败')
  } finally {
    loading.value = false
  }
}

// 文件选择
const handleFileChange: UploadProps['onChange'] = (uploadFile) => {
  selectedFile.value = uploadFile.raw as File
}

const handleExceed: UploadProps['onExceed'] = (files) => {
  uploadRef.value!.clearFiles()
  const file = files[0] as UploadRawFile
  uploadRef.value!.handleStart(file)
  selectedFile.value = file
}

// 上传并处理
const handleUpload = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  uploading.value = true
  uploadStep.value = 1
  
  try {
    const result: any = await uploadAndProcessTemplate(selectedFile.value)
    
    if (result.success) {
      previewData.value = result
      confirmForm.value.name = selectedFile.value.name.replace(/\.(docx?|doc)$/i, '')
      
      // 获取模板预览 Blob
      await loadPreviewBlob(result.temp_template_path)
      
      uploadStep.value = 2
      ElMessage.success('AI 处理完成')
    } else {
      throw new Error(result.error || '处理失败')
    }
  } catch (error: any) {
    console.error(error)
    ElMessage.error(error.response?.data?.detail || error.message || '模板处理失败')
    uploadStep.value = 0
  } finally {
    uploading.value = false
  }
}

// 加载模板预览 Blob
const loadPreviewBlob = async (tempPath: string) => {
  try {
    const token = localStorage.getItem('token')
    const response = await fetch(`/api/v1/templates/temp-preview?path=${encodeURIComponent(tempPath)}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (response.ok) {
      previewBlob.value = await response.blob()
    }
  } catch (error) {
    console.error('Load preview blob error:', error)
  }
}

const handlePreviewLoaded = () => {
  console.log('Template preview loaded')
}

const handlePreviewError = (error: string) => {
  console.error('Template preview error:', error)
}

// 确认保存
const handleConfirmSave = async () => {
  if (!confirmForm.value.name) {
    ElMessage.warning('请输入模板名称')
    return
  }
  if (!confirmForm.value.document_type) {
    ElMessage.warning('请选择文书类型')
    return
  }

  saving.value = true
  try {
    await confirmTemplate({
      name: confirmForm.value.name,
      document_type: confirmForm.value.document_type,
      temp_template_path: previewData.value.temp_template_path,
      temp_original_path: previewData.value.temp_original_path,
      fields: previewData.value.fields || {}
    })
    
    ElMessage.success('模板保存成功')
    handleCancelUpload()
    await loadTemplates()
  } catch (error: any) {
    console.error(error)
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

// 重新上传
const handleReupload = () => {
  uploadStep.value = 0
  selectedFile.value = null
  previewData.value = {}
  previewBlob.value = null
  confirmForm.value = { name: '', document_type: '' }
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

// 取消上传
const handleCancelUpload = () => {
  uploadDialogVisible.value = false
  handleReupload()
}

// 查看模板
const handleView = (row: any) => {
  viewTemplate.value = { ...row }
  viewDialogVisible.value = true
}

// 使用模板
const handleUse = (row: any) => {
  router.push({ path: '/generate', query: { templateId: row.id } })
}

const handleUseFromView = () => {
  viewDialogVisible.value = false
  router.push({ path: '/generate', query: { templateId: viewTemplate.value.id } })
}

// 删除模板
const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模板 "${row.name}" 吗？`,
      '提示',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    
    await deleteTemplate(row.id)
    ElMessage.success('模板已删除')
    await loadTemplates()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error(error)
      ElMessage.error('删除失败')
    }
  }
}

// 获取类型标签
const getTypeLabel = (type: string) => {
  const typeMap: Record<string, string> = {
    text: '文本',
    date: '日期',
    number: '数字'
  }
  return typeMap[type] || type
}

const formatDate = (date: string) => {
  if (!date) return '-'
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

.is-loading {
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 上传步骤 */
.upload-step {
  padding: 20px 0;
}

.template-upload {
  width: 100%;
}

.template-upload :deep(.el-upload-dragger) {
  width: 100%;
}

/* 处理中步骤 */
.processing-step {
  text-align: center;
  padding: 60px 0;
}

.processing-title {
  margin-top: 20px;
  font-size: 16px;
  color: #303133;
}

.processing-hint {
  color: #909399;
}

/* 确认步骤 - 左右分栏 */
.confirm-step {
  height: calc(100vh - 250px);
  min-height: 500px;
}

.confirm-layout {
  display: flex;
  gap: 20px;
  height: 100%;
}

.preview-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.info-panel {
  width: 450px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.panel-header {
  padding: 12px 16px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: #303133;
}

.preview-content {
  flex: 1;
  overflow: auto;
  background: #fafafa;
}

.info-content {
  flex: 1;
  overflow: auto;
  padding: 16px;
}

.confirm-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

code {
  background-color: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  color: #e6a23c;
}
</style>
