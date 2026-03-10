<template>
  <div class="settings">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>系统设置</span>
              <el-button type="primary" @click="saveSettings">
                <el-icon><Check /></el-icon>
                保存设置
              </el-button>
            </div>
          </template>
          
          <el-form label-width="150px">
            <el-form-item label="Docker Socket 路径">
              <el-input v-model="settings.docker_socket" placeholder="/var/run/docker.sock" />
              <div class="form-tip">Docker daemon socket 路径，Linux 通常为 /var/run/docker.sock，macOS 为 ~/.docker/run/docker.sock</div>
            </el-form-item>
            
            <el-form-item label="Web UI 访问端口">
              <el-input-number v-model="settings.web_port" :min="1" :max="65535" />
            </el-form-item>
            
            <el-form-item label="数据存储根目录">
              <el-input v-model="settings.data_root" placeholder="/data/openclaw" />
              <div class="form-tip">所有群组和实例数据将存储在此目录下</div>
            </el-form-item>
            
            <el-form-item label="默认 Docker 镜像">
              <el-input v-model="settings.default_image" placeholder="openclaw/openclaw:latest" />
              <div class="form-tip">创建新实例时使用的 Docker 镜像</div>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <span>Docker 镜像管理</span>
              <el-button type="primary" @click="pullImage" :loading="pulling">
                <el-icon><Download /></el-icon>
                预拉取镜像
              </el-button>
            </div>
          </template>
          <el-form label-width="150px">
            <el-form-item label="镜像地址">
              <el-input v-model="pullImageName" placeholder="openclaw/openclaw:latest" />
            </el-form-item>
          </el-form>
          <el-alert v-if="pullResult" :type="pullSuccess ? 'success' : 'error'" :closable="false" style="margin-top: 10px;">
            {{ pullResult }}
          </el-alert>
        </el-card>

        <el-card style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <span>Docker 镜像源配置</span>
              <el-button type="success" @click="saveDockerRegistry" :loading="savingRegistry">
                <el-icon><Check /></el-icon>
                保存配置
              </el-button>
            </div>
          </template>
          <el-form label-width="150px">
            <el-form-item label="镜像加速器">
              <el-select v-model="dockerRegistry.registry" placeholder="选择镜像源" style="width: 100%;" @change="onRegistryChange">
                <el-option label="官方 Docker Hub" value="" />
                <el-option label="阿里云容器镜像服务" value="registry.cn-hangzhou.aliyuncs.com" />
                <el-option label="Docker Proxy (GHCR)" value="ghcr.io" />
                <el-option label="Google Container Registry" value="gcr.io" />
                <el-option label="Quay.io" value="quay.io" />
                <el-option label="自定义" value="custom" />
              </el-select>
            </el-form-item>
            <el-form-item label="自定义镜像源" v-if="dockerRegistry.registry === 'custom'">
              <el-input v-model="dockerRegistry.customRegistry" placeholder="registry.example.com" />
            </el-form-item>
            <el-form-item label="加速器地址" v-if="dockerRegistry.registry">
              <el-input v-model="dockerRegistry.mirrorUrl" placeholder="https://mirror.example.com" />
              <div class="form-tip">Docker 镜像加速器地址，可留空使用默认加速</div>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>环境检测</span>
              <el-button @click="checkEnvironment" :loading="checking">
                <el-icon><Refresh /></el-icon>
                重新检测
              </el-button>
            </div>
          </template>
          <el-descriptions :column="1" border v-if="envCheck">
            <el-descriptions-item label="操作系统">{{ envCheck.os }}</el-descriptions-item>
            <el-descriptions-item label="系统版本">{{ envCheck.os_version }}</el-descriptions-item>
            <el-descriptions-item label="CPU 架构">{{ envCheck.architecture }}</el-descriptions-item>
            <el-descriptions-item label="Python 版本">{{ envCheck.python_version }}</el-descriptions-item>
            <el-descriptions-item label="Docker 可用">
              <el-tag :type="envCheck.docker_available ? 'success' : 'danger'">
                {{ envCheck.docker_available ? '可用' : '不可用' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="Docker 版本">{{ envCheck.docker_version || '未知' }}</el-descriptions-item>
            <el-descriptions-item label="Docker Socket">
              <el-tag :type="envCheck.docker_socket_exists ? 'success' : 'warning'">
                {{ envCheck.docker_socket_exists ? '存在' : '不存在' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="数据目录可写">
              <el-tag :type="envCheck.data_dir_writable ? 'success' : 'danger'">
                {{ envCheck.data_dir_writable ? '可写' : '只读' }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <span>Docker 网络列表</span>
              <el-button @click="loadNetworks" :loading="loadingNetworks">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </template>
          <el-table :data="dockerNetworks" v-if="dockerNetworks.length > 0" max-height="200">
            <el-table-column prop="name" label="网络名称" />
            <el-table-column prop="id" label="网络ID">
              <template #default="{ row }">
                {{ row.id ? row.id.substring(0, 12) : 'N/A' }}
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="暂无 Docker 网络" :image-size="60" />
        </el-card>

        <el-card style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <span>Docker 镜像列表</span>
              <el-button @click="loadImages" :loading="loadingImages">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </template>
          <el-table :data="dockerImages" v-if="dockerImages.length > 0" max-height="250">
            <el-table-column label="镜像名称">
              <template #default="{ row }">
                <div v-if="row.tags && row.tags.length > 0">
                  <el-tag v-for="tag in row.tags" :key="tag" size="small" style="margin-right: 5px;">{{ tag }}</el-tag>
                </div>
                <span v-else>{{ row.short_id }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="short_id" label="ID" width="120">
              <template #default="{ row }">
                {{ row.short_id }}
              </template>
            </el-table-column>
            <el-table-column label="大小" width="120">
              <template #default="{ row }">
                {{ formatBytes(row.size) }}
              </template>
            </el-table-column>
            <el-table-column label="创建时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.created) }}
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="暂无 Docker 镜像" :image-size="60" />
        </el-card>

        <el-card style="margin-top: 20px;">
          <template #header>
            <span>Docker 环境信息</span>
          </template>
          <el-descriptions :column="2" border v-if="dockerInfo">
            <el-descriptions-item label="Docker 版本">{{ dockerInfo.docker_version }}</el-descriptions-item>
            <el-descriptions-item label="CPU 核心数">{{ dockerInfo.cpus }}</el-descriptions-item>
            <el-descriptions-item label="容器总数">{{ dockerInfo.containers }}</el-descriptions-item>
            <el-descriptions-item label="运行中容器">{{ dockerInfo.containers_running }}</el-descriptions-item>
            <el-descriptions-item label="镜像数量">{{ dockerInfo.images }}</el-descriptions-item>
            <el-descriptions-item label="内存总量">{{ formatBytes(dockerInfo.memory_total) }}</el-descriptions-item>
          </el-descriptions>
          <el-empty v-else description="无法获取 Docker 信息" />
        </el-card>

        <el-card style="margin-top: 20px;">
          <template #header>
            <span>环境信息</span>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="操作系统">{{ osInfo.os }}</el-descriptions-item>
            <el-descriptions-item label="主机名">{{ osInfo.hostname }}</el-descriptions-item>
            <el-descriptions-item label="后端版本">1.0.0</el-descriptions-item>
            <el-descriptions-item label="前端版本">1.0.0</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card style="margin-top: 20px;">
          <template #header>
            <span>关于</span>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="项目名称">OpenClaw Manager</el-descriptions-item>
            <el-descriptions-item label="项目描述">OpenClaw 多实例群组化部署管理系统</el-descriptions-item>
            <el-descriptions-item label="技术栈">FastAPI + Vue3 + Element Plus + SQLite</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { systemApi } from '../api'

const settings = ref({
  docker_socket: '/var/run/docker.sock',
  web_port: 8080,
  data_root: '/data/openclaw',
  default_image: 'openclaw/openclaw:latest'
})

const dockerInfo = ref(null)
const osInfo = ref({
  os: 'Unknown',
  hostname: 'Unknown'
})

const envCheck = ref(null)
const checking = ref(false)
const pulling = ref(false)
const pullImageName = ref('openclaw/openclaw:latest')
const pullResult = ref('')
const pullSuccess = ref(false)
const savingRegistry = ref(false)
const loadingNetworks = ref(false)
const loadingImages = ref(false)
const dockerNetworks = ref([])
const dockerImages = ref([])

const dockerRegistry = ref({
  registry: '',
  customRegistry: '',
  mirrorUrl: ''
})

const loadSettings = async () => {
  try {
    const res = await systemApi.getSettings()
    settings.value = { ...settings.value, ...res }
  } catch (error) {
    ElMessage.error('获取设置失败')
  }
}

const loadDockerInfo = async () => {
  try {
    const stats = await systemApi.getStats()
    dockerInfo.value = stats.docker
  } catch (error) {
    console.error('获取 Docker 信息失败', error)
  }
}

const checkEnvironment = async () => {
  checking.value = true
  try {
    envCheck.value = await systemApi.checkEnv()
  } catch (error) {
    ElMessage.error('环境检测失败: ' + error)
  } finally {
    checking.value = false
  }
}

const pullImage = async () => {
  if (!pullImageName.value) {
    ElMessage.warning('请输入镜像地址')
    return
  }
  pulling.value = true
  pullResult.value = ''
  try {
    await systemApi.pullImage(pullImageName.value)
    pullSuccess.value = true
    pullResult.value = '镜像拉取成功: ' + pullImageName.value
    ElMessage.success('镜像拉取成功')
  } catch (error) {
    pullSuccess.value = false
    pullResult.value = '镜像拉取失败: ' + error
    ElMessage.error('镜像拉取失败: ' + error)
  } finally {
    pulling.value = false
  }
}

const saveSettings = async () => {
  try {
    await systemApi.updateSettings(settings.value)
    ElMessage.success('设置保存成功')
  } catch (error) {
    ElMessage.error('保存设置失败: ' + error)
  }
}

const saveDockerRegistry = async () => {
  savingRegistry.value = true
  try {
    const registrySettings = {
      docker_registry: dockerRegistry.value.registry || dockerRegistry.value.customRegistry || '',
      docker_mirror: dockerRegistry.value.mirrorUrl || ''
    }
    const currentSettings = await systemApi.getSettings()
    await systemApi.updateSettings({ ...currentSettings, ...registrySettings })
    ElMessage.success('镜像源配置保存成功')
  } catch (error) {
    ElMessage.error('保存镜像源配置失败: ' + error)
  } finally {
    savingRegistry.value = false
  }
}

const onRegistryChange = () => {
  const presets = {
    'registry.cn-hangzhou.ali': 'https://registry.cnyuncs.com-hangzhou.aliyuncs.com',
    'ghcr.io': '',
    'gcr.io': '',
    'quay.io': ''
  }
  if (dockerRegistry.value.registry && presets[dockerRegistry.value.registry] !== undefined) {
    dockerRegistry.value.mirrorUrl = presets[dockerRegistry.value.registry]
  }
}

const loadNetworks = async () => {
  loadingNetworks.value = true
  try {
    const res = await systemApi.getNetworks()
    dockerNetworks.value = res.networks || []
  } catch (error) {
    console.error('获取网络列表失败', error)
    dockerNetworks.value = []
  } finally {
    loadingNetworks.value = false
  }
}

const loadImages = async () => {
  loadingImages.value = true
  try {
    const res = await systemApi.getImages()
    dockerImages.value = res.images || []
  } catch (error) {
    console.error('获取镜像列表失败', error)
    dockerImages.value = []
  } finally {
    loadingImages.value = false
  }
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

const formatDate = (timestamp) => {
  if (!timestamp) return 'N/A'
  const date = new Date(timestamp * 1000)
  return date.toLocaleString('zh-CN')
}

const detectOs = () => {
  const platform = navigator.platform.toLowerCase()
  if (platform.includes('mac')) {
    osInfo.value.os = 'macOS'
  } else if (platform.includes('win')) {
    osInfo.value.os = 'Windows'
  } else if (platform.includes('linux')) {
    osInfo.value.os = 'Linux'
  } else {
    osInfo.value.os = platform
  }
  
  osInfo.value.hostname = window.location.hostname || 'localhost'
}

onMounted(() => {
  loadSettings()
  loadDockerInfo()
  detectOs()
  checkEnvironment()
  loadNetworks()
  loadImages()
})
</script>

<style scoped>
.settings {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}
</style>
