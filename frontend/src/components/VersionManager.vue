<template>
  <div class="version-manager">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>版本历史</span>
          <el-button size="small" @click="loadVersions">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <el-timeline v-if="versions.length > 0">
        <el-timeline-item
          v-for="version in versions"
          :key="version.id"
          :timestamp="formatDate(version.created_at)"
          placement="top"
        >
          <el-card>
            <div class="version-header">
              <el-tag :type="version.is_rollback ? 'warning' : 'primary'">
                版本 {{ version.version_number }}
              </el-tag>
              <el-tag v-if="version.is_rollback" type="warning" size="small">
                回滚版本
              </el-tag>
            </div>
            
            <p class="version-description">
              {{ version.change_description || '无变更说明' }}
            </p>

            <div class="version-actions">
              <el-button-group>
                <el-button size="small" @click="viewVersion(version)">
                  <el-icon><View /></el-icon>
                  查看
                </el-button>
                <el-button 
                  size="small" 
                  @click="compareWithCurrent(version)"
                  :disabled="version.version_number === currentVersion"
                >
                  <el-icon><DocumentCopy /></el-icon>
                  对比
                </el-button>
                <el-button 
                  size="small" 
                  type="warning"
                  @click="confirmRollback(version)"
                  :disabled="version.version_number === currentVersion"
                >
                  <el-icon><RefreshLeft /></el-icon>
                  回滚
                </el-button>
              </el-button-group>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>

      <el-empty v-else description="暂无版本历史" />
    </el-card>

    <!-- 版本详情对话框 -->
    <el-dialog v-model="detailVisible" title="版本详情" width="60%">
      <div v-if="selectedVersion">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="版本号">
            {{ selectedVersion.version_number }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDate(selectedVersion.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="变更说明" :span="2">
            {{ selectedVersion.change_description }}
          </el-descriptions-item>
        </el-descriptions>
        
        <el-divider>文档内容</el-divider>
        <div class="version-content">
          {{ selectedVersion.content }}
        </div>
      </div>
    </el-dialog>

    <!-- 版本对比对话框 -->
    <el-dialog v-model="compareVisible" title="版本对比" width="80%" top="5vh">
      <div v-if="compareResult">
        <el-alert
          :title="`版本 ${compareResult.version1_number} vs 版本 ${compareResult.version2_number}`"
          type="info"
          :closable="false"
          style="margin-bottom: 20px"
        />

        <el-tabs v-model="compareTab">
          <el-tab-pane label="摘要" name="summary">
            <el-card>
              <p><strong>对比摘要：</strong></p>
              <p>{{ compareResult.summary }}</p>
              
              <el-divider />
              
              <div v-if="compareResult.highlights && compareResult.highlights.length > 0">
                <p><strong>主要变更：</strong></p>
                <el-tag
                  v-for="(highlight, index) in compareResult.highlights"
                  :key="index"
                  :type="getHighlightType(highlight.type)"
                  style="margin: 5px"
                >
                  {{ highlight.description }}
                </el-tag>
              </div>
            </el-card>
          </el-tab-pane>

          <el-tab-pane label="文本差异" name="text" v-if="compareResult.text_diff">
            <el-card>
              <el-statistic-group>
                <el-statistic title="新增行数" :value="compareResult.text_diff.added_count" />
                <el-statistic title="删除行数" :value="compareResult.text_diff.removed_count" />
                <el-statistic title="相似度" :value="compareResult.text_diff.similarity" suffix="%" />
              </el-statistic-group>
            </el-card>
          </el-tab-pane>

          <el-tab-pane label="字段差异" name="fields" v-if="compareResult.fields_diff">
            <el-card>
              <el-statistic-group>
                <el-statistic title="新增字段" :value="compareResult.fields_diff.added_count" />
                <el-statistic title="删除字段" :value="compareResult.fields_diff.removed_count" />
                <el-statistic title="修改字段" :value="compareResult.fields_diff.modified_count" />
              </el-statistic-group>
              
              <el-divider />
              
              <div v-if="compareResult.fields_diff.modified_fields">
                <h4>修改的字段：</h4>
                <el-descriptions :column="1" border>
                  <el-descriptions-item
                    v-for="(change, field) in compareResult.fields_diff.modified_fields"
                    :key="field"
                    :label="field"
                  >
                    <div>
                      <p><strong>旧值：</strong>{{ change.old_value }}</p>
                      <p><strong>新值：</strong>{{ change.new_value }}</p>
                    </div>
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </el-card>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>

    <!-- 回滚确认对话框 -->
    <el-dialog v-model="rollbackVisible" title="确认回滚" width="500px">
      <el-alert
        title="警告"
        type="warning"
        description="回滚操作将创建一个新版本，内容为选定版本的内容。此操作不可撤销。"
        :closable="false"
        show-icon
        style="margin-bottom: 20px"
      />
      
      <el-form :model="rollbackForm" label-width="100px">
        <el-form-item label="目标版本">
          版本 {{ rollbackForm.target_version }}
        </el-form-item>
        <el-form-item label="回滚原因">
          <el-input
            v-model="rollbackForm.rollback_reason"
            type="textarea"
            :rows="3"
            placeholder="请输入回滚原因（可选）"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="rollbackVisible = false">取消</el-button>
        <el-button type="warning" @click="handleRollback" :loading="rolling">
          确认回滚
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Refresh, View, DocumentCopy, RefreshLeft } from '@element-plus/icons-vue'
import { getVersionList, getVersionDetail, compareVersions, rollbackVersion } from '@/api/versions'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  documentId: number
  currentVersion?: number
}>()

const emit = defineEmits(['refresh'])

const versions = ref<any[]>([])
const selectedVersion = ref<any>(null)
const compareResult = ref<any>(null)
const detailVisible = ref(false)
const compareVisible = ref(false)
const rollbackVisible = ref(false)
const compareTab = ref('summary')
const rolling = ref(false)

const rollbackForm = ref({
  target_version: 0,
  rollback_reason: ''
})

const loadVersions = async () => {
  try {
    const data: any = await getVersionList(props.documentId)
    versions.value = data
  } catch (error) {
    console.error(error)
    ElMessage.error('加载版本列表失败')
  }
}

const viewVersion = async (version: any) => {
  try {
    const data = await getVersionDetail(version.id)
    selectedVersion.value = data
    detailVisible.value = true
  } catch (error) {
    console.error(error)
    ElMessage.error('加载版本详情失败')
  }
}

const compareWithCurrent = async (version: any) => {
  if (versions.value.length < 2) {
    ElMessage.warning('至少需要两个版本才能对比')
    return
  }

  try {
    const currentVer = versions.value[0].version_number
    const data = await compareVersions({
      document_id: props.documentId,
      version1: version.version_number,
      version2: currentVer,
      compare_type: 'full'
    })
    compareResult.value = data
    compareVisible.value = true
  } catch (error) {
    console.error(error)
    ElMessage.error('版本对比失败')
  }
}

const confirmRollback = (version: any) => {
  rollbackForm.value = {
    target_version: version.version_number,
    rollback_reason: ''
  }
  rollbackVisible.value = true
}

const handleRollback = async () => {
  rolling.value = true
  try {
    await rollbackVersion({
      document_id: props.documentId,
      target_version: rollbackForm.value.target_version,
      rollback_reason: rollbackForm.value.rollback_reason
    })
    ElMessage.success('回滚成功')
    rollbackVisible.value = false
    await loadVersions()
    emit('refresh')
  } catch (error) {
    console.error(error)
    ElMessage.error('回滚失败')
  } finally {
    rolling.value = false
  }
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

const getHighlightType = (type: string) => {
  const map: any = {
    added: 'success',
    removed: 'danger',
    modified: 'warning'
  }
  return map[type] || 'info'
}

onMounted(() => {
  loadVersions()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.version-header {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.version-description {
  margin: 10px 0;
  color: #666;
}

.version-actions {
  margin-top: 10px;
}

.version-content {
  max-height: 400px;
  overflow-y: auto;
  padding: 15px;
  background-color: #f5f5f5;
  border-radius: 4px;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
