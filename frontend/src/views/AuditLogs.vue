<template>
  <div class="audit-logs-page">
    <!-- 统计卡片 -->
    <el-row :gutter="20" style="margin-bottom: 20px">
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="总操作数" :value="stats.total_count" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="上传文件" :value="stats.action_stats.upload || 0" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="AI 研判" :value="stats.action_stats.review || 0" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="生成文书" :value="stats.action_stats.generate || 0" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 查询表单 -->
    <el-card style="margin-bottom: 20px">
      <el-form :model="queryForm" inline>
        <el-form-item label="操作类型">
          <el-select v-model="queryForm.action" placeholder="全部" clearable style="width: 150px">
            <el-option label="上传" value="upload" />
            <el-option label="研判" value="review" />
            <el-option label="生成" value="generate" />
            <el-option label="编辑" value="update" />
            <el-option label="下载" value="download" />
            <el-option label="删除" value="delete" />
            <el-option label="回滚" value="rollback" />
          </el-select>
        </el-form-item>

        <el-form-item label="资源类型">
          <el-select v-model="queryForm.resource_type" placeholder="全部" clearable style="width: 150px">
            <el-option label="文件" value="file" />
            <el-option label="文书" value="document" />
            <el-option label="模板" value="template" />
          </el-select>
        </el-form-item>

        <el-form-item label="日期范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 280px"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
          <el-button @click="handleExport">
            <el-icon><Download /></el-icon>
            导出
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 日志列表 -->
    <el-card>
      <template #header>
        <span>审计日志</span>
      </template>

      <el-table 
        ref="tableRef"
        :data="logList" 
        v-loading="loading" 
        stripe 
        border
        style="width: 100%"
      >
        <el-table-column type="index" label="序号" width="70" align="center" />
        <el-table-column prop="username" label="用户" min-width="100" show-overflow-tooltip />
        <el-table-column label="操作" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getActionType(row.action)" size="small">
              {{ getActionText(row.action) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="资源类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.resource_type" type="info" size="small">
              {{ getResourceText(row.resource_type) }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="resource_id" label="资源ID" min-width="90" align="center" />
        <el-table-column prop="ip_address" label="IP地址" min-width="140" show-overflow-tooltip />
        <el-table-column label="操作时间" min-width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90" align="center" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleViewDetail(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSearch"
        @current-change="handleSearch"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="日志详情" width="700px">
      <el-descriptions v-if="currentLog" :column="2" border>
        <el-descriptions-item label="ID">{{ currentLog.id }}</el-descriptions-item>
        <el-descriptions-item label="用户">{{ currentLog.username }}</el-descriptions-item>
        <el-descriptions-item label="操作">
          <el-tag :type="getActionType(currentLog.action)">
            {{ getActionText(currentLog.action) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="资源类型">
          {{ getResourceText(currentLog.resource_type) || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="资源ID">
          {{ currentLog.resource_id || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="IP地址">
          {{ currentLog.ip_address || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="操作时间" :span="2">
          {{ formatDate(currentLog.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="User Agent" :span="2">
          <div style="word-break: break-all; max-height: 100px; overflow-y: auto">
            {{ currentLog.user_agent || '-' }}
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="详细信息" :span="2">
          <pre style="max-height: 300px; overflow-y: auto; background: #f5f5f5; padding: 10px; border-radius: 4px">{{ JSON.stringify(currentLog.details, null, 2) }}</pre>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { Search, Refresh, Download } from '@element-plus/icons-vue'
import { getAuditLogList, getAuditStats } from '@/api/auditLogs'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const logList = ref<any[]>([])
const stats = ref<any>({
  total_count: 0,
  action_stats: {},
  resource_stats: {}
})
const dateRange = ref<string[]>([])
const queryForm = ref({
  action: '',
  resource_type: ''
})
const pagination = ref({
  page: 1,
  page_size: 20,
  total: 0
})
const detailVisible = ref(false)
const currentLog = ref<any>(null)
const tableRef = ref()

const loadStats = async () => {
  try {
    const data: any = await getAuditStats(7)
    stats.value = data
  } catch (error) {
    console.error(error)
  }
}

const loadLogs = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.value.page,
      page_size: pagination.value.page_size
    }

    if (queryForm.value.action) {
      params.action = queryForm.value.action
    }

    if (queryForm.value.resource_type) {
      params.resource_type = queryForm.value.resource_type
    }

    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }

    const data: any = await getAuditLogList(params)
    console.log('Audit logs data:', data)
    console.log('Items:', data.items)
    logList.value = data.items || []
    pagination.value.total = data.total || 0
    
    // 强制表格重新布局
    await nextTick()
    if (tableRef.value) {
      tableRef.value.doLayout()
    }
    // 触发窗口 resize 事件，让表格重新计算列宽
    window.dispatchEvent(new Event('resize'))
  } catch (error) {
    console.error('Load logs error:', error)
    ElMessage.error('加载日志失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.value.page = 1
  loadLogs()
}

const handleReset = () => {
  queryForm.value = {
    action: '',
    resource_type: ''
  }
  dateRange.value = []
  handleSearch()
}

const handleExport = () => {
  const params: any = {}

  if (queryForm.value.action) {
    params.action = queryForm.value.action
  }

  if (queryForm.value.resource_type) {
    params.resource_type = queryForm.value.resource_type
  }

  if (dateRange.value && dateRange.value.length === 2) {
    params.start_date = dateRange.value[0]
    params.end_date = dateRange.value[1]
  }

  // 获取 token
  const authStore = useAuthStore()
  const token = authStore.token
  
  if (!token) {
    ElMessage.error('请先登录')
    return
  }

  // 构建 URL
  const baseUrl = 'http://localhost:8000/api/v1/audit-logs/export'
  const queryString = new URLSearchParams(params).toString()
  const url = `${baseUrl}${queryString ? '?' + queryString : ''}`
  
  // 使用 fetch 下载，带上 token
  fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  })
    .then(response => {
      if (!response.ok) {
        throw new Error('导出失败')
      }
      return response.blob()
    })
    .then(blob => {
      // 创建下载链接
      const downloadUrl = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = `audit_logs_${new Date().getTime()}.csv`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(downloadUrl)
      ElMessage.success('导出成功')
    })
    .catch(error => {
      console.error(error)
      ElMessage.error('导出失败')
    })
}

const handleViewDetail = (row: any) => {
  currentLog.value = row
  detailVisible.value = true
}

const getActionType = (action: string) => {
  const map: any = {
    upload: 'primary',
    review: 'success',
    generate: 'warning',
    update: 'info',
    download: '',
    delete: 'danger',
    rollback: 'warning'
  }
  return map[action] || ''
}

const getActionText = (action: string) => {
  const map: any = {
    upload: '上传',
    review: '研判',
    generate: '生成',
    update: '编辑',
    download: '下载',
    delete: '删除',
    rollback: '回滚',
    batch_upload: '批量上传'
  }
  return map[action] || action
}

const getResourceText = (resourceType: string) => {
  const map: any = {
    file: '文件',
    document: '文书',
    template: '模板'
  }
  return map[resourceType] || resourceType
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

onMounted(() => {
  loadStats()
  loadLogs()
})
</script>

<style scoped>
.audit-logs-page {
  padding: 20px;
}
</style>
