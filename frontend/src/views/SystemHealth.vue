<template>
  <div class="system-health-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>系统健康监控</span>
          <el-button @click="refreshData" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <el-row :gutter="20">
        <!-- 健康状态卡片 -->
        <el-col :span="12">
          <el-card shadow="hover" class="status-card">
            <template #header>
              <div class="card-title">
                <el-icon><Monitor /></el-icon>
                <span>服务状态</span>
              </div>
            </template>

            <div v-if="healthStatus" class="status-content">
              <div class="status-item">
                <span class="label">运行模式：</span>
                <el-tag :type="healthStatus.mode === 'normal' ? 'success' : 'warning'" size="large">
                  {{ healthStatus.mode === 'normal' ? '正常模式' : '降级模式' }}
                </el-tag>
              </div>

              <div class="status-item">
                <span class="label">AI 服务：</span>
                <el-tag :type="healthStatus.ai_service_available ? 'success' : 'danger'">
                  {{ healthStatus.ai_service_available ? '可用' : '不可用' }}
                </el-tag>
              </div>

              <div class="status-item">
                <span class="label">连续失败次数：</span>
                <span class="value">{{ healthStatus.consecutive_failures }}</span>
              </div>

              <div class="status-item">
                <span class="label">连续成功次数：</span>
                <span class="value">{{ healthStatus.consecutive_successes }}</span>
              </div>

              <div class="status-item">
                <span class="label">最后检查时间：</span>
                <span class="value">{{ formatTime(healthStatus.last_check_time) }}</span>
              </div>

              <div v-if="healthStatus.fallback_start_time" class="status-item">
                <span class="label">降级开始时间：</span>
                <span class="value">{{ formatTime(healthStatus.fallback_start_time) }}</span>
              </div>

              <div v-if="healthStatus.estimated_recovery_time" class="status-item">
                <span class="label">预计恢复时间：</span>
                <span class="value">{{ formatTime(healthStatus.estimated_recovery_time) }}</span>
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- 降级统计卡片 -->
        <el-col :span="12">
          <el-card shadow="hover" class="stats-card">
            <template #header>
              <div class="card-title">
                <el-icon><DataAnalysis /></el-icon>
                <span>降级统计</span>
              </div>
            </template>

            <div v-if="fallbackStats" class="stats-content">
              <div class="stat-item">
                <div class="stat-value">{{ fallbackStats.total_checks }}</div>
                <div class="stat-label">总检查次数</div>
              </div>

              <div class="stat-item">
                <div class="stat-value error">{{ fallbackStats.total_failures }}</div>
                <div class="stat-label">总失败次数</div>
              </div>

              <div class="stat-item">
                <div class="stat-value warning">{{ fallbackStats.total_fallback_events }}</div>
                <div class="stat-label">降级事件</div>
              </div>

              <div v-if="fallbackStats.current_fallback_duration" class="stat-item">
                <div class="stat-value">{{ formatDuration(fallbackStats.current_fallback_duration) }}</div>
                <div class="stat-label">当前降级时长</div>
              </div>

              <div v-if="fallbackStats.average_fallback_duration" class="stat-item">
                <div class="stat-value">{{ formatDuration(fallbackStats.average_fallback_duration) }}</div>
                <div class="stat-label">平均降级时长</div>
              </div>

              <div v-if="fallbackStats.last_fallback_time" class="stat-item full-width">
                <div class="stat-label">最后降级时间</div>
                <div class="stat-value small">{{ formatTime(fallbackStats.last_fallback_time) }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 健康状态时间线 -->
      <el-card shadow="hover" style="margin-top: 20px;">
        <template #header>
          <div class="card-title">
            <el-icon><TrendCharts /></el-icon>
            <span>健康状态历史</span>
          </div>
        </template>

        <el-timeline>
          <el-timeline-item
            v-for="(event, index) in healthHistory"
            :key="index"
            :timestamp="formatTime(event.timestamp)"
            :type="event.type"
            :icon="event.icon"
          >
            {{ event.message }}
          </el-timeline-item>
        </el-timeline>

        <el-empty v-if="healthHistory.length === 0" description="暂无历史记录" />
      </el-card>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { Refresh, Monitor, DataAnalysis, TrendCharts } from '@element-plus/icons-vue'
import { getHealthStatus, getFallbackStats, type HealthStatus, type FallbackStats } from '@/api/health'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const healthStatus = ref<HealthStatus | null>(null)
const fallbackStats = ref<FallbackStats | null>(null)
const healthHistory = ref<any[]>([])
const checkInterval = ref<number | null>(null)

const loadHealthStatus = async () => {
  try {
    const data = await getHealthStatus()
    const newStatus = data as any
    
    // 检测状态变化并添加到历史
    if (healthStatus.value && healthStatus.value.mode !== newStatus.mode) {
      healthHistory.value.unshift({
        timestamp: new Date().toISOString(),
        type: newStatus.mode === 'normal' ? 'success' : 'warning',
        icon: newStatus.mode === 'normal' ? 'SuccessFilled' : 'WarningFilled',
        message: newStatus.mode === 'normal' 
          ? 'AI 服务已恢复，切换到正常模式'
          : 'AI 服务不可用，切换到降级模式'
      })
      
      // 只保留最近 20 条记录
      if (healthHistory.value.length > 20) {
        healthHistory.value = healthHistory.value.slice(0, 20)
      }
    }
    
    healthStatus.value = newStatus
  } catch (error) {
    console.error('Failed to load health status:', error)
  }
}

const loadFallbackStats = async () => {
  try {
    const data = await getFallbackStats()
    fallbackStats.value = data as any
  } catch (error) {
    console.error('Failed to load fallback stats:', error)
  }
}

const refreshData = async () => {
  loading.value = true
  try {
    await Promise.all([loadHealthStatus(), loadFallbackStats()])
    ElMessage.success('数据已刷新')
  } catch (error) {
    ElMessage.error('刷新失败')
  } finally {
    loading.value = false
  }
}

const formatTime = (time: string) => {
  if (!time) return '-'
  try {
    const date = new Date(time)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch {
    return time
  }
}

const formatDuration = (seconds: number) => {
  if (!seconds) return '-'
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours}小时${minutes}分钟`
  } else if (minutes > 0) {
    return `${minutes}分钟${secs}秒`
  } else {
    return `${secs}秒`
  }
}

onMounted(() => {
  refreshData()
  // 每 30 秒自动刷新
  checkInterval.value = window.setInterval(() => {
    loadHealthStatus()
    loadFallbackStats()
  }, 30000)
})

onUnmounted(() => {
  if (checkInterval.value) {
    clearInterval(checkInterval.value)
  }
})
</script>

<style scoped>
.system-health-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.status-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.status-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.status-item .label {
  font-weight: 500;
  color: #606266;
}

.status-item .value {
  color: #303133;
}

.stats-content {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.stat-item {
  text-align: center;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.stat-item.full-width {
  grid-column: 1 / -1;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 8px;
}

.stat-value.error {
  color: #F56C6C;
}

.stat-value.warning {
  color: #E6A23C;
}

.stat-value.small {
  font-size: 16px;
  margin-top: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}
</style>
