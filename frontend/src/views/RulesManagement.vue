<template>
  <div class="rules-management-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>规则管理</span>
          <div class="header-actions">
            <el-button @click="loadRulesPerformance">
              <el-icon><DataLine /></el-icon>
              性能分析
            </el-button>
            <el-button type="primary" @click="handleReloadRules" :loading="reloading">
              <el-icon><Refresh /></el-icon>
              重载配置
            </el-button>
          </div>
        </div>
      </template>

      <!-- 统计信息 -->
      <el-row :gutter="20" style="margin-bottom: 20px;">
        <el-col :span="6">
          <el-statistic title="总规则数" :value="statistics?.total_rules || 0">
            <template #prefix>
              <el-icon><Document /></el-icon>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="6">
          <el-statistic title="已启用" :value="statistics?.enabled_rules || 0">
            <template #prefix>
              <el-icon style="color: #67C23A;"><CircleCheck /></el-icon>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="6">
          <el-statistic title="已禁用" :value="statistics?.disabled_rules || 0">
            <template #prefix>
              <el-icon style="color: #F56C6C;"><CircleClose /></el-icon>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="6">
          <el-statistic title="规则类别" :value="Object.keys(statistics?.rules_by_category || {}).length">
            <template #prefix>
              <el-icon><FolderOpened /></el-icon>
            </template>
          </el-statistic>
        </el-col>
      </el-row>

      <!-- 规则列表 -->
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="规则列表" name="list">
          <el-table :data="filteredRules" v-loading="loading" stripe>
            <el-table-column prop="id" label="规则ID" width="150" />
            <el-table-column prop="name" label="规则名称" width="200" />
            <el-table-column prop="description" label="描述" show-overflow-tooltip />
            <el-table-column prop="category" label="类别" width="120">
              <template #default="{ row }">
                <el-tag :type="getCategoryType(row.category)" size="small">
                  {{ getCategoryName(row.category) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag size="small">{{ row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="priority" label="优先级" width="80" align="center" />
            <el-table-column prop="enabled" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-switch
                  v-model="row.enabled"
                  @change="handleToggleRule(row)"
                  :loading="row.toggling"
                />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" align="center">
              <template #default="{ row }">
                <el-button
                  size="small"
                  @click="showRuleDetail(row)"
                  link
                >
                  详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="性能分析" name="performance">
          <el-table :data="performanceData" v-loading="performanceLoading" stripe>
            <el-table-column prop="rule_name" label="规则名称" width="200" />
            <el-table-column prop="execution_count" label="执行次数" width="120" align="center" />
            <el-table-column prop="average_time" label="平均耗时(ms)" width="150" align="center">
              <template #default="{ row }">
                <span :class="{ 'slow-rule': row.is_slow }">
                  {{ (row.average_time * 1000).toFixed(2) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="max_time" label="最大耗时(ms)" width="150" align="center">
              <template #default="{ row }">
                {{ (row.max_time * 1000).toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="min_time" label="最小耗时(ms)" width="150" align="center">
              <template #default="{ row }">
                {{ (row.min_time * 1000).toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="total_time" label="总耗时(s)" width="120" align="center">
              <template #default="{ row }">
                {{ row.total_time.toFixed(3) }}
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.is_slow" type="warning" size="small">慢规则</el-tag>
                <el-tag v-else type="success" size="small">正常</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="分类统计" name="statistics">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-card shadow="hover">
                <template #header>按类别统计</template>
                <div class="stat-list">
                  <div
                    v-for="(count, category) in statistics?.rules_by_category"
                    :key="category"
                    class="stat-item"
                  >
                    <span class="stat-label">{{ getCategoryName(category) }}</span>
                    <el-tag>{{ count }} 个规则</el-tag>
                  </div>
                </div>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card shadow="hover">
                <template #header>按类型统计</template>
                <div class="stat-list">
                  <div
                    v-for="(count, type) in statistics?.rules_by_type"
                    :key="type"
                    class="stat-item"
                  >
                    <span class="stat-label">{{ type }}</span>
                    <el-tag>{{ count }} 个规则</el-tag>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 规则详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="规则详情" width="600px">
      <div v-if="selectedRule" class="rule-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="规则ID">{{ selectedRule.id }}</el-descriptions-item>
          <el-descriptions-item label="规则名称">{{ selectedRule.name }}</el-descriptions-item>
          <el-descriptions-item label="描述">{{ selectedRule.description }}</el-descriptions-item>
          <el-descriptions-item label="类别">
            <el-tag :type="getCategoryType(selectedRule.category)">
              {{ getCategoryName(selectedRule.category) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="类型">{{ selectedRule.type }}</el-descriptions-item>
          <el-descriptions-item label="优先级">{{ selectedRule.priority }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="selectedRule.enabled ? 'success' : 'danger'">
              {{ selectedRule.enabled ? '已启用' : '已禁用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedRule.pattern" label="匹配模式">
            <code>{{ selectedRule.pattern }}</code>
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedRule.min_length" label="最小长度">
            {{ selectedRule.min_length }}
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedRule.max_length" label="最大长度">
            {{ selectedRule.max_length }}
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedRule.keywords" label="关键词">
            <el-tag v-for="keyword in selectedRule.keywords" :key="keyword" size="small" style="margin-right: 5px;">
              {{ keyword }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  Refresh,
  DataLine,
  Document,
  CircleCheck,
  CircleClose,
  FolderOpened
} from '@element-plus/icons-vue'
import {
  getRulesList,
  getRulesPerformance,
  getRulesStatistics,
  toggleRule,
  reloadRules,
  type Rule,
  type RulePerformance,
  type RuleStatistics
} from '@/api/admin'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const performanceLoading = ref(false)
const reloading = ref(false)
const activeTab = ref('list')
const rules = ref<Rule[]>([])
const performanceData = ref<RulePerformance[]>([])
const statistics = ref<RuleStatistics | null>(null)
const detailDialogVisible = ref(false)
const selectedRule = ref<Rule | null>(null)

const filteredRules = computed(() => {
  return rules.value
})

const loadRules = async () => {
  loading.value = true
  try {
    const data = await getRulesList()
    // 后端返回的是 { rules: [...], total_rules: ..., enabled_rules: ..., disabled_rules: ... }
    const response = data as any
    rules.value = (response.rules || []).map((rule: Rule) => ({
      ...rule,
      toggling: false
    }))
  } catch (error) {
    console.error('Failed to load rules:', error)
    ElMessage.error('加载规则列表失败')
  } finally {
    loading.value = false
  }
}

const loadRulesPerformance = async () => {
  performanceLoading.value = true
  activeTab.value = 'performance'
  try {
    const data = await getRulesPerformance()
    // 后端返回的是 { rule_metrics: [...], total_validations: ..., ... }
    const response = data as any
    performanceData.value = response.rule_metrics || []
  } catch (error) {
    console.error('Failed to load performance:', error)
    ElMessage.error('加载性能数据失败')
  } finally {
    performanceLoading.value = false
  }
}

const loadStatistics = async () => {
  try {
    const data = await getRulesStatistics()
    statistics.value = data as any
  } catch (error) {
    console.error('Failed to load statistics:', error)
  }
}

const handleToggleRule = async (rule: any) => {
  rule.toggling = true
  try {
    await toggleRule(rule.id, rule.enabled)
    ElMessage.success(`规则已${rule.enabled ? '启用' : '禁用'}`)
    await loadStatistics()
  } catch (error) {
    console.error('Failed to toggle rule:', error)
    rule.enabled = !rule.enabled
    ElMessage.error('操作失败')
  } finally {
    rule.toggling = false
  }
}

const handleReloadRules = async () => {
  try {
    await ElMessageBox.confirm('确定要重载规则配置吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    reloading.value = true
    await reloadRules()
    ElMessage.success('规则配置已重载')
    await loadRules()
    await loadStatistics()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to reload rules:', error)
      ElMessage.error('重载失败')
    }
  } finally {
    reloading.value = false
  }
}

const showRuleDetail = (rule: Rule) => {
  selectedRule.value = rule
  detailDialogVisible.value = true
}

const handleTabChange = (tab: string) => {
  if (tab === 'performance' && performanceData.value.length === 0) {
    loadRulesPerformance()
  }
}

const getCategoryType = (category: string) => {
  const map: Record<string, any> = {
    format: 'primary',
    content: 'success',
    compliance: 'warning'
  }
  return map[category] || 'info'
}

const getCategoryName = (category: string) => {
  const map: Record<string, string> = {
    format: '格式规则',
    content: '内容规则',
    compliance: '合规性规则'
  }
  return map[category] || category
}

onMounted(() => {
  loadRules()
  loadStatistics()
})
</script>

<style scoped>
.rules-management-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.slow-rule {
  color: #E6A23C;
  font-weight: bold;
}

.stat-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.stat-label {
  font-weight: 500;
  color: #606266;
}

.rule-detail code {
  padding: 2px 6px;
  background-color: #f5f7fa;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}
</style>
