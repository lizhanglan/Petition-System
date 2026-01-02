<template>
  <el-alert
    v-if="showNotice"
    :title="noticeTitle"
    :type="noticeType"
    :description="noticeDescription"
    :closable="false"
    show-icon
    class="fallback-notice"
  >
    <template #default>
      <div class="notice-content">
        <p>{{ noticeDescription }}</p>
        <div v-if="healthStatus?.estimated_recovery_time" class="recovery-info">
          <el-icon><Clock /></el-icon>
          <span>预计恢复时间：{{ formatRecoveryTime(healthStatus.estimated_recovery_time) }}</span>
        </div>
      </div>
    </template>
  </el-alert>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Clock } from '@element-plus/icons-vue'
import { getHealthStatus, type HealthStatus } from '@/api/health'

const healthStatus = ref<HealthStatus | null>(null)
const checkInterval = ref<number | null>(null)

const showNotice = computed(() => {
  return healthStatus.value?.mode === 'fallback'
})

const noticeType = computed(() => {
  return healthStatus.value?.mode === 'fallback' ? 'warning' : 'success'
})

const noticeTitle = computed(() => {
  if (healthStatus.value?.mode === 'fallback') {
    return 'AI 服务暂时不可用，已切换到本地规则引擎'
  }
  return 'AI 服务正常'
})

const noticeDescription = computed(() => {
  if (healthStatus.value?.mode === 'fallback') {
    return '系统已自动切换到本地规则引擎进行文档验证，功能不受影响。AI 服务恢复后将自动切换回来。'
  }
  return ''
})

const loadHealthStatus = async () => {
  try {
    const data = await getHealthStatus()
    healthStatus.value = data as any
  } catch (error) {
    console.error('Failed to load health status:', error)
  }
}

const formatRecoveryTime = (time: string) => {
  try {
    const date = new Date(time)
    return date.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return time
  }
}

onMounted(() => {
  loadHealthStatus()
  // 每 30 秒检查一次健康状态
  checkInterval.value = window.setInterval(loadHealthStatus, 30000)
})

onUnmounted(() => {
  if (checkInterval.value) {
    clearInterval(checkInterval.value)
  }
})
</script>

<style scoped>
.fallback-notice {
  margin-bottom: 20px;
}

.notice-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.recovery-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #606266;
}

.recovery-info .el-icon {
  font-size: 16px;
}
</style>
