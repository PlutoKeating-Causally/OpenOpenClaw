<template>
  <div class="groups">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>群组列表</span>
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            创建群组
          </el-button>
        </div>
      </template>
      
      <el-table :data="groups" style="width: 100%" @row-click="viewGroup">
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="root_dir" label="根目录" />
        <el-table-column prop="docker_network" label="Docker网络" />
        <el-table-column label="端口范围">
          <template #default="{ row }">
            {{ row.port_range_start }} - {{ row.port_range_end }}
          </template>
        </el-table-column>
        <el-table-column prop="instance_count" label="实例数" width="80" />
        <el-table-column prop="description" label="描述" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click.stop="editGroup(row)">编辑</el-button>
            <el-button size="small" type="danger" @click.stop="confirmDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="群组名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入群组名称" />
        </el-form-item>
        <el-form-item label="根目录" prop="root_dir">
          <el-input v-model="form.root_dir" placeholder="groups/xxx">
            <template #prepend v-if="effectiveDataRoot">{{ effectiveDataRoot }}/</template>
          </el-input>
          <div class="form-tip" v-if="effectiveDataRoot">数据物理路径：{{ effectiveDataRoot }}/{{ form.root_dir }}</div>
        </el-form-item>
        <el-form-item label="Docker网络" prop="docker_network">
          <el-input v-model="form.docker_network" placeholder="openclaw_network_xxx" />
        </el-form-item>
        <el-form-item label="端口范围" prop="port_range">
          <el-input-number v-model="form.port_range_start" :min="1" :max="65535" />
          <span style="margin: 0 10px;">-</span>
          <el-input-number v-model="form.port_range_end" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="drawerVisible" :title="selectedGroup?.name" size="60%">
      <el-descriptions :column="2" border v-if="selectedGroup">
        <el-descriptions-item label="名称">{{ selectedGroup.name }}</el-descriptions-item>
        <el-descriptions-item label="Docker网络">{{ selectedGroup.docker_network }}</el-descriptions-item>
        <el-descriptions-item label="根目录">{{ selectedGroup.root_dir }}</el-descriptions-item>
        <el-descriptions-item label="端口范围">{{ selectedGroup.port_range_start }} - {{ selectedGroup.port_range_end }}</el-descriptions-item>
        <el-descriptions-item label="存储使用">{{ formatSize(selectedGroup.storage_used) }}</el-descriptions-item>
      </el-descriptions>
      
      <div style="margin: 15px 0;">
        <el-button type="primary" @click="editGroupConfig">
          <el-icon><Setting /></el-icon>
          配置编辑
        </el-button>
      </div>
      
      <el-divider>实例列表</el-divider>
      
      <el-table :data="selectedGroup?.instances || []" style="width: 100%">
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="row.status === 'running' ? 'success' : 'info'">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="host_port" label="端口" />
        <el-table-column prop="created_at" label="创建时间" />
      </el-table>
    </el-drawer>

    <OperationLog ref="operationLog" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { groupApi, systemApi } from '../api'
import OperationLog from '../components/OperationLog.vue'

const router = useRouter()
const operationLog = ref(null)

const groups = ref([])
const dialogVisible = ref(false)
const drawerVisible = ref(false)
const formRef = ref(null)
const selectedGroup = ref(null)
const effectiveDataRoot = ref('')

const form = ref({
  name: '',
  root_dir: '',
  docker_network: '',
  port_range_start: 18790,
  port_range_end: 18800,
  description: ''
})

const rules = {
  name: [{ required: true, message: '请输入群组名称', trigger: 'blur' }],
  root_dir: [{ required: true, message: '请输入根目录', trigger: 'blur' }],
  docker_network: [{ required: true, message: '请输入Docker网络名称', trigger: 'blur' }]
}

const dialogTitle = computed(() => form.value.id ? '编辑群组' : '创建群组')

const loadGroups = async () => {
  try {
    groups.value = await groupApi.getAll()
  } catch (error) {
    ElMessage.error('获取群组列表失败')
  }
}

const showCreateDialog = () => {
  form.value = {
    name: '',
    root_dir: 'groups/',
    docker_network: 'openclaw_network_',
    port_range_start: 18980,
    port_range_end: 18990,
    description: ''
  }
  dialogVisible.value = true
}

// Watch name to auto-fill relative root_dir
watch(() => form.value.name, (newName) => {
  if (!form.value.id && newName) {
    // Only auto-fill if the user hasn't modified the default 'groups/' part too much
    if (form.value.root_dir === 'groups/' || form.value.root_dir.startsWith('groups/')) {
      form.value.root_dir = `groups/${newName}`
    }
  }
})

const editGroup = (row) => {
  form.value = { ...row }
  dialogVisible.value = true
}

const submitForm = async () => {
  const valid = await formRef.value?.validate()
  if (!valid) return
  
  try {
    if (form.value.id) {
      await groupApi.update(form.value.id, {
        name: form.value.name,
        root_dir: form.value.root_dir,
        docker_network: form.value.docker_network,
        description: form.value.description,
        port_range_start: form.value.port_range_start,
        port_range_end: form.value.port_range_end
      })
      ElMessage.success('群组更新成功')
    } else {
      dialogVisible.value = false
      await operationLog.value.execute(`创建群组: ${form.value.name}`, async (addLog) => {
        addLog(`群组名称: ${form.value.name}`, 'info')
        addLog(`根目录: ${form.value.root_dir}`, 'info')
        addLog(`Docker 网络: ${form.value.docker_network}`, 'info')
        return await groupApi.create(form.value)
      })
      ElMessage.success('群组创建成功')
    }
    dialogVisible.value = false
    loadGroups()
  } catch (error) {
    ElMessage.error(error)
  }
}

const confirmDelete = (row) => {
  ElMessageBox.confirm(
    `确定要删除群组 "${row.name}" 吗？这将同时删除群组内的所有实例。`,
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await operationLog.value.execute(`删除群组: ${row.name}`, async (addLog) => {
        addLog(`群组 ID: ${row.id}`, 'info')
        addLog(`Docker 网络: ${row.docker_network}`, 'info')
        return await groupApi.delete(row.id)
      })
      ElMessage.success('群组删除成功')
      loadGroups()
    } catch (error) {
      ElMessage.error('删除失败: ' + error)
    }
  }).catch(() => {})
}

const viewGroup = async (row) => {
  try {
    selectedGroup.value = await groupApi.getById(row.id)
    drawerVisible.value = true
  } catch (error) {
    ElMessage.error('获取群组详情失败')
  }
}

const formatSize = (bytes) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  while (bytes >= 1024 && i < units.length - 1) {
    bytes /= 1024
    i++
  }
  return `${bytes.toFixed(2)} ${units[i]}`
}

const editGroupConfig = () => {
  router.push({ path: '/config', query: { type: 'group', id: selectedGroup.value.id } })
}

onMounted(async () => {
  loadGroups()
  try {
    const settings = await systemApi.getSettings()
    effectiveDataRoot.value = settings.effective_data_dir || settings.data_root || '/data/openclaw'
  } catch (error) {
    console.error('获取设置失败', error)
  }
})
</script>

<style scoped>
.groups {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
