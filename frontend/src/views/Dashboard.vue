<template>
  <div class="dashboard">
    <h2>工作台</h2>
    
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background-color: #409EFF;">📄</div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.files }}</div>
              <div class="stat-label">上传文件</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background-color: #67C23A;">📝</div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.documents }}</div>
              <div class="stat-label">生成文书</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background-color: #E6A23C;">📋</div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.templates }}</div>
              <div class="stat-label">模板数量</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background-color: #F56C6C;">✓</div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.reviewed }}</div>
              <div class="stat-label">已审核</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>快速操作</span>
          </template>
          <div class="quick-actions">
            <el-button type="primary" @click="$router.push('/files')">上传文件</el-button>
            <el-button type="success" @click="$router.push('/generate')">生成文书</el-button>
            <el-button type="warning" @click="$router.push('/templates')">管理模板</el-button>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>系统说明</span>
          </template>
          <div class="system-info">
            <p>✓ 支持 PDF、Word 文件上传与预览</p>
            <p>✓ AI 智能文书研判与标注</p>
            <p>✓ 对话式文书生成</p>
            <p>✓ 版本管理与精细化回滚</p>
            <p>✓ 模板智能识别与管理</p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getFileList } from '@/api/files'
import { getDocumentList } from '@/api/documents'
import { getTemplateList } from '@/api/templates'

const stats = ref({
  files: 0,
  documents: 0,
  templates: 0,
  reviewed: 0
})

onMounted(async () => {
  try {
    const [files, documents, templates] = await Promise.all([
      getFileList(0, 1000),
      getDocumentList(0, 1000),
      getTemplateList(undefined, 0, 1000)
    ])
    
    stats.value.files = files.length
    stats.value.documents = documents.length
    stats.value.templates = templates.length
    stats.value.reviewed = files.filter((f: any) => f.status === 'reviewed').length
  } catch (error) {
    console.error(error)
  }
})
</script>

<style scoped>
.dashboard h2 {
  margin-bottom: 20px;
}

.stat-card {
  cursor: pointer;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-content {
  display: flex;
  align-items: center;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30px;
  margin-right: 15px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #999;
  margin-top: 5px;
}

.quick-actions {
  display: flex;
  gap: 10px;
}

.system-info p {
  margin: 10px 0;
  color: #666;
}
</style>
