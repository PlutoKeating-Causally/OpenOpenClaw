<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #409eff;">
              <el-icon :size="30"><Box /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_instances }}</div>
              <div class="stat-label">实例总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #67c23a;">
              <el-icon :size="30"><VideoPlay /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.running_instances }}</div>
              <div class="stat-label">运行中</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #909399;">
              <el-icon :size="30"><VideoPause /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.stopped_instances }}</div>
              <div class="stat-label">已停止</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #e6a23c;">
              <el-icon :size="30"><Folder /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_groups }}</div>
              <div class="stat-label">群组数量</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card class="action-card">
          <template #header>
            <div class="card-header">
              <span>快速操作</span>
            </div>
          </template>
          <div class="quick-actions">
            <el-button type="primary" @click="$router.push('/groups')">
              <el-icon><Plus /></el-icon>
              创建群组
            </el-button>
            <el-button type="success" @click="startAll">
              <el-icon><VideoPlay /></el-icon>
              启动全部
            </el-button>
            <el-button type="warning" @click="stopAll">
              <el-icon><VideoPause /></el-icon>
              停止全部
            </el-button>
            <el-button @click="$router.push('/instances')">
              <el-icon><List /></el-icon>
              查看实例
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <span>Docker 状态</span>
            </div>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="容器总数">{{ stats.docker?.containers || 0 }}</el-descriptions-item>
            <el-descriptions-item label="运行中">{{ stats.docker?.containers_running || 0 }}</el-descriptions-item>
            <el-descriptions-item label="已暂停">{{ stats.docker?.containers_paused || 0 }}</el-descriptions-item>
            <el-descriptions-item label="已停止">{{ stats.docker?.containers_stopped || 0 }}</el-descriptions-item>
            <el-descriptions-item label="镜像数量">{{ stats.docker?.images || 0 }}</el-descriptions-item>
            <el-descriptions-item label="CPU 核心">{{ stats.docker?.cpus || 0 }}</el-descriptions-item>
            <el-descriptions-item label="内存总量">{{ formatBytes(stats.docker?.memory_total) }}</el-descriptions-item>
            <el-descriptions-item label="Docker 版本">{{ stats.docker?.docker_version || '未知' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <span>运行中实例资源</span>
              <el-button size="small" @click="loadResourceStats">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </template>
          <div v-if="runningInstances.length === 0" style="text-align: center; color: #909399; padding: 20px;">
            暂无运行中的实例
          </div>
          <el-table v-else :data="runningInstances" style="width: 100%" max-height="280">
            <el-table-column prop="name" label="实例" />
            <el-table-column prop="group_name" label="群组" width="100" />
            <el-table-column label="CPU" width="100">
              <template #default="{ row }">
                <el-progress 
                  :percentage="row.cpu_percent || 0" 
                  :color="getCpuColor(row.cpu_percent)"
                  :stroke-width="10"
                  style="width: 60px;"
                />
              </template>
            </el-table-column>
            <el-table-column label="内存" width="150">
              <template #default="{ row }">
                <el-progress 
                  :percentage="row.memory_percent || 0" 
                  :color="getMemoryColor(row.memory_percent)"
                  :stroke-width="10"
                />
                <span style="font-size: 11px; color: #909399;">
                  {{ formatBytes(row.memory_usage) }} / {{ formatBytes(row.memory_limit) }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { groupApi, instanceApi, systemApi } from '../api'

const stats = ref({
  total_instances: 0,
  running_instances: 0,
  stopped_instances: 0,
  total_groups: 0,
  docker: {}
})

const instances = ref([])
const runningInstances = ref([])
let refreshTimer = null

const loadStats = async () => {
  try {
    stats.value = await systemApi.getStats()
  } catch (error) {
    ElMessage.error('获取统计数据失败')
  }
}

const loadInstances = async () => {
  try {
    instances.value = await instanceApi.getAll()
    await loadResourceStats()
  } catch (error) {
    ElMessage.error('获取实例列表失败')
  }
}

const loadResourceStats = async () => {
  const running = instances.value.filter(i => i.status === 'running')
  const results = []
  for (const inst of running) {
    try {
      const resourceStats = await instanceApi.getStats(inst.id)
      results.push({
        ...inst,
        cpu_percent: resourceStats.cpu_percent || 0,
        memory_usage: resourceStats.memory_usage || 0,
        memory_limit: resourceStats.memory_limit || 0,
        memory_percent: resourceStats.memory_percent || 0
      })
    } catch (error) {
      results.push({
        ...inst,
        cpu_percent: 0,
        memory_usage: 0,
        memory_limit: 0,
        memory_percent: 0
      })
    }
  }
  runningInstances.value = results
}

const formatBytes = (bytes) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let i = 0
  while (bytes >= 1024 && i < units.length - 1) {
    bytes /= 1024
    i++
  }
  return `${bytes.toFixed(2)} ${units[i]}`
}

const getCpuColor = (percent) => {
  if (percent < 50) return '#67c23a'
  if (percent < 80) return '#e6a23c'
  return '#f56c6c'
}

const getMemoryColor = (percent) => {
  if (percent < 50) return '#67c23a'
  if (percent < 80) return '#e6a23c'
  return '#f56c6c'
}

const startInstance = async (id) => {
  try {
    await instanceApi.start(id)
    ElMessage.success('实例已启动')
    loadStats()
    loadInstances()
  } catch (error) {
    ElMessage.error('启动实例失败: ' + error)
  }
}

const stopInstance = async (id) => {
  try {
    await instanceApi.stop(id)
    ElMessage.success('实例已停止')
    loadStats()
    loadInstances()
  } catch (error) {
    ElMessage.error('停止实例失败: ' + error)
  }
}

const startAll = async () => {
  try {
    const result = await instanceApi.startAll()
    ElMessage.success(result.message || '批量启动完成')
    loadStats()
    loadInstances()
  } catch (error) {
    ElMessage.error('批量启动失败: ' + error)
  }
}

const stopAll = async () => {
  try {
    const result = await instanceApi.stopAll()
    ElMessage.success(result.message || '批量停止完成')
    loadStats()
    loadInstances()
  } catch (error) {
    ElMessage.error('批量停止失败: ' + error)
  }
}

onMounted(() => {
  loadStats()
  loadInstances()
  refreshTimer = setInterval(() => {
    loadStats()
    loadInstances()
  }, 5000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.stat-card {
  margin-bottom: 0;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #999;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 16px;
}

.quick-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.info-card {
  height: 100%;
}
</style>
