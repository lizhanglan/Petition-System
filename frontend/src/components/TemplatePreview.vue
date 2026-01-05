<template>
  <div class="template-preview">
    <!-- 字段列表 -->
    <div class="fields-section">
      <h4>识别的字段</h4>
      <el-table :data="fieldsList" border size="small">
        <el-table-column prop="name" label="变量名" width="160" />
        <el-table-column prop="label" label="中文名称" />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ getTypeLabel(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="required" label="必填" width="80">
          <template #default="{ row }">
            <el-tag :type="row.required ? 'danger' : 'info'" size="small">
              {{ row.required ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 替换映射 -->
    <div v-if="replacements && Object.keys(replacements).length > 0" class="replacements-section">
      <h4>替换映射</h4>
      <el-table :data="replacementsList" border size="small">
        <el-table-column prop="original" label="原文内容" />
        <el-table-column prop="placeholder" label="占位符" width="200">
          <template #default="{ row }">
            <code>{{ row.placeholder }}</code>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 模板预览（如果有模板文件路径） -->
    <div v-if="templatePath" class="docx-preview-section">
      <h4>模板预览</h4>
      <DocxPreview :file-url="templatePreviewUrl" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import DocxPreview from './DocxPreview.vue'

interface Props {
  fields: Record<string, any>
  replacements?: Record<string, string>
  templatePath?: string
}

const props = defineProps<Props>()

// 将 fields 对象转换为数组
const fieldsList = computed(() => {
  if (!props.fields) return []
  return Object.entries(props.fields).map(([name, info]: [string, any]) => ({
    name,
    label: info.label || name,
    type: info.type || 'text',
    required: info.required || false,
    description: info.description || ''
  }))
})

// 将 replacements 对象转换为数组
const replacementsList = computed(() => {
  if (!props.replacements) return []
  return Object.entries(props.replacements).map(([original, placeholder]) => ({
    original,
    placeholder
  }))
})

// 获取类型标签
const getTypeLabel = (type: string) => {
  const typeMap: Record<string, string> = {
    text: '文本',
    date: '日期',
    number: '数字'
  }
  return typeMap[type] || type
}

// 模板预览 URL
const templatePreviewUrl = computed(() => {
  if (!props.templatePath) return ''
  const token = localStorage.getItem('token')
  // 这里需要根据实际情况调整 URL
  return `/api/v1/templates/preview-file?path=${encodeURIComponent(props.templatePath)}`
})
</script>

<style scoped>
.template-preview {
  padding: 10px 0;
}

.fields-section,
.replacements-section,
.docx-preview-section {
  margin-bottom: 20px;
}

.fields-section h4,
.replacements-section h4,
.docx-preview-section h4 {
  margin-bottom: 10px;
  color: #303133;
  font-size: 14px;
}

code {
  background-color: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  color: #e6a23c;
}
</style>
