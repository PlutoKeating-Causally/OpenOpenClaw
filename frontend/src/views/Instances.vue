<template>
  <div class="instances">
    <el-card>
      <template #header>
        <div class="card-header">
          <div>
            <el-select v-model="filterGroup" placeholder="筛选群组" clearable style="width: 200px; margin-right: 10px;">
              <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
            </el-select>
            <el-button type="primary" @click="showCreateDialog">
              <el-icon><Plus /></el-icon>
              创建实例
            </el-button>
          </div>
          <div>
            <el-button-group>
              <el-button type="success" @click="batchStart" :disabled="selectedIds.length === 0">批量启动</el-button>
              <el-button type="warning" @click="batchStop" :disabled="selectedIds.length === 0">批量停止</el-button>
              <el-button type="danger" @click="batchDelete" :disabled="selectedIds.length === 0">批量删除</el-button>
            </el-button-group>
          </div>
        </div>
      </template>
      
      <el-table 
        :data="filteredInstances" 
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="group_name" label="群组" />
        <el-table-column prop="host_port" label="端口" width="80" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'running' ? 'success' : row.status === 'exited' ? 'danger' : 'info'">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" />
        <el-table-column label="操作" width="320">
          <template #default="{ row }">
            <el-button size="small" type="success" v-if="row.status !== 'running'" @click="startInstance(row.id)">启动</el-button>
            <el-button size="small" type="warning" v-else @click="stopInstance(row.id)">停止</el-button>
            <el-button size="small" @click="restartInstance(row.id)" :disabled="row.status !== 'running'">重启</el-button>
            <el-button size="small" @click="viewInstance(row)">详情</el-button>
            <el-button size="small" @click="openTerminal(row)" :disabled="row.status !== 'running'">终端</el-button>
            <el-button size="small" type="info" @click="showCloneDialog(row)">克隆</el-button>
            <el-button size="small" type="danger" @click="confirmDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="创建实例" width="500px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="所属群组" prop="group_id">
          <el-select v-model="form.group_id" placeholder="请选择群组" style="width: 100%;">
            <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="实例名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入实例名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="drawerVisible" title="实例详情" size="60%">
      <template v-if="selectedInstance">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="名称">{{ selectedInstance.name }}</el-descriptions-item>
          <el-descriptions-item label="群组">{{ selectedInstance.group_name }}</el-descriptions-item>
          <el-descriptions-item label="容器名">{{ selectedInstance.container_name }}</el-descriptions-item>
          <el-descriptions-item label="端口">{{ selectedInstance.host_port }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="selectedInstance.status === 'running' ? 'success' : 'info'">
              {{ selectedInstance.status }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ selectedInstance.created_at }}</el-descriptions-item>
        </el-descriptions>

        <el-divider>资源监控</el-divider>
        <el-row :gutter="20" v-if="instanceStats.cpu_percent !== undefined">
          <el-col :span="12">
            <el-progress :percentage="instanceStats.cpu_percent" :color="getCpuColor(instanceStats.cpu_percent)">
              <span>CPU: {{ instanceStats.cpu_percent }}%</span>
            </el-progress>
          </el-col>
          <el-col :span="12">
            <el-progress :percentage="instanceStats.memory_percent" :color="getMemoryColor(instanceStats.memory_percent)">
              <span>内存: {{ formatBytes(instanceStats.memory_usage) }} / {{ formatBytes(instanceStats.memory_limit) }}</span>
            </el-progress>
          </el-col>
        </el-row>
        <el-button @click="refreshStats" size="small" style="margin-top: 10px;">
          <el-icon><Refresh /></el-icon>
          刷新资源
        </el-button>

        <el-divider>容器信息</el-divider>
        <el-descriptions :column="2" border v-if="selectedInstance.container_info">
          <el-descriptions-item label="镜像">{{ selectedInstance.container_info.image }}</el-descriptions-item>
          <el-descriptions-item label="容器ID">{{ selectedInstance.container_info.id?.substring(0, 12) }}</el-descriptions-item>
          <el-descriptions-item label="网络">{{ selectedInstance.container_info.networks?.join(', ') }}</el-descriptions-item>
        </el-descriptions>

        <el-divider>运行日志</el-divider>
        <el-button @click="refreshLogs" size="small" style="margin-bottom: 10px;">
          <el-icon><Refresh /></el-icon>
          刷新日志
        </el-button>
        <pre class="log-content">{{ selectedInstance.logs || '暂无日志' }}</pre>

        <el-divider>配置预览</el-divider>
        <el-button type="primary" @click="editInstanceConfig" style="margin-bottom: 10px;">
          <el-icon><Setting /></el-icon>
          编辑配置
        </el-button>
        <el-tabs v-model="configTab">
          <el-tab-pane label="环境变量" name="env">
            <pre class="config-content">{{ formatJson(selectedInstance.config?.env) }}</pre>
          </el-tab-pane>
          <el-tab-pane label="openclaw.json" name="openclaw">
            <pre class="config-content">{{ formatJson(selectedInstance.config?.openclaw) }}</pre>
          </el-tab-pane>
        </el-tabs>
      </template>
    </el-drawer>

    <el-dialog v-model="cloneDialogVisible" title="克隆实例" width="400px">
      <el-form label-width="100px">
        <el-form-item label="源实例">
          <el-input :value="cloneSourceInstance?.name" disabled />
        </el-form-item>
        <el-form-item label="新实例名称" prop="cloneName">
          <el-input v-model="cloneName" placeholder="输入新实例名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cloneDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmClone">确定克隆</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { groupApi, instanceApi } from '../api'

const route = useRoute()
const router = useRouter()

const groups = ref([])
const instances = ref([])
const filterGroup = ref('')
const selectedIds = ref([])
const dialogVisible = ref(false)
const drawerVisible = ref(false)
const formRef = ref(null)
const selectedInstance = ref(null)
const configTab = ref('env')
const cloneDialogVisible = ref(false)
const cloneSourceInstance = ref(null)
const cloneName = ref('')
const instanceStats = ref({})

const form = ref({
  group_id: '',
  name: ''
})

const rules = {
  group_id: [{ required: true, message: '请选择群组', trigger: 'change' }],
  name: [{ required: true, message: '请输入实例名称', trigger: 'blur' }]
}

const filteredInstances = computed(() => {
  if (!filterGroup.value) return instances.value
  return instances.value.filter(i => i.group_id === filterGroup.value)
})

const loadGroups = async () => {
  try {
    groups.value = await groupApi.getAll()
  } catch (error) {
    ElMessage.error('获取群组列表失败')
  }
}

const loadInstances = async () => {
  try {
    instances.value = await instanceApi.getAll(filterGroup.value || undefined)
  } catch (error) {
    ElMessage.error('获取实例列表失败')
  }
}

watch(() => route.params.groupId, (newVal) => {
  if (newVal) {
    filterGroup.value = newVal
  }
}, { immediate: true })

const showCreateDialog = () => {
  form.value = {
    group_id: filterGroup.value || (groups.value[0]?.id || ''),
    name: ''
  }
  dialogVisible.value = true
}

const submitForm = async () => {
  const valid = await formRef.value?.validate()
  if (!valid) return
  
  try {
    await instanceApi.create(form.value)
    ElMessage.success('实例创建成功')
    dialogVisible.value = false
    loadInstances()
  } catch (error) {
    ElMessage.error(error)
  }
}

const restartInstance = async (id) => {
  try {
    await instanceApi.restart(id)
    ElMessage.success('实例已重启')
    loadInstances()
  } catch (error) {
    ElMessage.error('重启失败: ' + error)
  }
}

const openTerminal = async (row) => {
  try {
    const result = await instanceApi.getTerminal(row.id)
    window.open(result.terminal_url || result.gateway_url, '_blank')
  } catch (error) {
    ElMessage.error('打开终端失败: ' + error)
  }
}

const showCloneDialog = (row) => {
  cloneSourceInstance.value = row
  cloneName.value = row.name + '-clone'
  cloneDialogVisible.value = true
}

const confirmClone = async () => {
  if (!cloneName.value) {
    ElMessage.warning('请输入新实例名称')
    return
  }
  try {
    await instanceApi.clone(cloneSourceInstance.value.id, cloneName.value)
    ElMessage.success('实例克隆成功')
    cloneDialogVisible.value = false
    loadInstances()
  } catch (error) {
    ElMessage.error('克隆失败: ' + error)
  }
}

const refreshStats = async () => {
  if (!selectedInstance.value) return
  try {
    instanceStats.value = await instanceApi.getStats(selectedInstance.value.id)
  } catch (error) {
    console.error('获取资源统计失败', error)
    instanceStats.value = {}
  }
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

const formatBytes = (bytes) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  while (bytes >= 1024 && i < units.length - 1) {
    bytes /= 1024
    i++
  }
  return `${bytes.toFixed(2)} ${units[i]}`
}

const viewInstance = async (row) => {
  try {
    selectedInstance.value = await instanceApi.getById(row.id)
    drawerVisible.value = true
    refreshStats()
  } catch (error) {
    ElMessage.error('获取实例详情失败')
  }
}

const refreshLogs = async () => {
  if (!selectedInstance.value) return
  try {
    const logs = await instanceApi.getLogs(selectedInstance.value.id)
    selectedInstance.value.logs = logs.logs
  } catch (error) {
    ElMessage.error('获取日志失败')
  }
}

const startInstance = async (id) => {
  try {
    await instanceApi.start(id)
    ElMessage.success('实例已启动')
    loadInstances()
  } catch (error) {
    ElMessage.error('启动失败: ' + error)
  }
}

const stopInstance = async (id) => {
  try {
    await instanceApi.stop(id)
    ElMessage.success('实例已停止')
    loadInstances()
  } catch (error) {
    ElMessage.error('停止失败: ' + error)
  }
}

const confirmDelete = (row) => {
  ElMessageBox.confirm(
    `确定要删除实例 "${row.name}" 吗？这将彻底清理容器和数据。`,
    '警告',
    { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
  ).then(async () => {
    try {
      await instanceApi.delete(row.id)
      ElMessage.success('实例删除成功')
      loadInstances()
    } catch (error) {
      ElMessage.error('删除失败: ' + error)
    }
  }).catch(() => {})
}

const handleSelectionChange = (selection) => {
  selectedIds.value = selection.map(s => s.id)
}

const batchStart = async () => {
  try {
    await instanceApi.batchStart(selectedIds.value)
    ElMessage.success('批量启动完成')
    loadInstances()
  } catch (error) {
    ElMessage.error('批量启动失败: ' + error)
  }
}

const batchStop = async () => {
  try {
    await instanceApi.batchStop(selectedIds.value)
    ElMessage.success('批量停止完成')
    loadInstances()
  } catch (error) {
    ElMessage.error('批量停止失败: ' + error)
  }
}

const batchDelete = async () => {
  await ElMessageBox.confirm(`确定要删除选中的 ${selectedIds.value.length} 个实例吗？`, '警告', 
    { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
  ).then(async () => {
    try {
      await instanceApi.batchDelete(selectedIds.value)
      ElMessage.success('批量删除完成')
      loadInstances()
    } catch (error) {
      ElMessage.error('批量删除失败: ' + error)
    }
  }).catch(() => {})
}

const formatJson = (obj) => {
  if (!obj) return '{}'
  try {
    return JSON.stringify(obj, null, 2)
  } catch {
    return String(obj)
  }
}

const editInstanceConfig = () => {
  router.push({ path: '/config', query: { type: 'instance', id: selectedInstance.value.id } })
}

onMounted(() => {
  loadGroups()
  loadInstances()
})
</script>

<style scoped>
.instances {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-content {
  background: #1a1a2e;
  color: #67c23a;
  padding: 15px;
  border-radius: 4px;
  max-height: 300px;
  overflow: auto;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
}

.config-content {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  max-height: 300px;
  overflow: auto;
  font-size: 12px;
  white-space: pre-wrap;
}
</style>
