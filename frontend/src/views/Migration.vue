<template>
  <div class="migration">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>导出</span>
            </div>
          </template>
          
          <el-tabs v-model="exportTab">
            <el-tab-pane label="导出实例" name="instance">
              <el-form label-width="100px">
                <el-form-item label="选择实例">
                  <el-select v-model="exportInstanceId" placeholder="选择要导出的实例" style="width: 100%;">
                    <el-option v-for="i in instances" :key="i.id" :label="`${i.name} (${i.group_name})`" :value="i.id" />
                  </el-select>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="exportInstance" :disabled="!exportInstanceId">
                    <el-icon><Download /></el-icon>
                    导出实例
                  </el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <el-tab-pane label="导出群组" name="group">
              <el-form label-width="100px">
                <el-form-item label="选择群组">
                  <el-select v-model="exportGroupId" placeholder="选择要导出的群组" style="width: 100%;">
                    <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
                  </el-select>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="exportGroup" :disabled="!exportGroupId">
                    <el-icon><Download /></el-icon>
                    导出群组
                  </el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>导入</span>
            </div>
          </template>
          
          <el-tabs v-model="importTab">
            <el-tab-pane label="从ZIP文件导入" name="file">
              <el-form label-width="100px">
                <el-form-item label="选择文件">
                  <el-upload
                    ref="uploadRef"
                    :auto-upload="false"
                    :limit="1"
                    :on-change="handleFileChange"
                    accept=".zip"
                    drag
                  >
                    <el-icon class="el-icon--upload"><Upload /></el-icon>
                    <div class="el-upload__text">
                      拖拽文件到此处或<em>点击上传</em>
                    </div>
                    <template #tip>
                      <div class="el-upload__tip">仅支持 .zip 文件</div>
                    </template>
                  </el-upload>
                </el-form-item>
                <el-form-item label="目标群组">
                  <el-select v-model="importGroupId" placeholder="选择目标群组" style="width: 100%;">
                    <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
                  </el-select>
                </el-form-item>
                <el-form-item label="实例名称">
                  <el-input v-model="importInstanceName" placeholder="输入新实例名称" style="width: 100%;" />
                </el-form-item>
                <el-form-item>
                  <el-button type="success" @click="uploadInstance" :disabled="!selectedFile || !importGroupId || !importInstanceName" :loading="uploading">
                    <el-icon><Upload /></el-icon>
                    上传并导入
                  </el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <el-tab-pane label="从目录导入" name="directory">
              <el-form label-width="100px">
                <el-form-item label="实例根目录">
                  <div style="display: flex; gap: 10px;">
                    <el-input v-model="importSourceDir" placeholder="请选择或输入实例根目录（映射为容器内 /root）" style="flex: 1" />
                    <el-button @click="handleBrowse">
                      <el-icon><Folder /></el-icon>
                      浏览
                    </el-button>
                  </div>
                  <div class="form-tip">选择已有 OpenClaw 实例的本地根目录（将映射为容器内 /root）</div>
                </el-form-item>
                <el-form-item label="目标群组">
                  <el-select v-model="importGroupIdDir" placeholder="选择目标群组" style="width: 100%;">
                    <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
                  </el-select>
                </el-form-item>
                <el-form-item label="实例名称">
                  <el-input v-model="importInstanceNameDir" placeholder="输入新实例名称" style="width: 100%;" />
                </el-form-item>
                <el-form-item>
                  <el-button type="success" @click="importFromDirectory" :disabled="!importSourceDir || !importGroupIdDir || !importInstanceNameDir">
                    <el-icon><Folder /></el-icon>
                    从目录导入
                  </el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <el-tab-pane label="导入群组" name="group">
              <el-form label-width="100px">
                <el-form-item label="群组文件">
                  <el-upload
                    ref="groupUploadRef"
                    :auto-upload="false"
                    :limit="1"
                    :on-change="handleGroupFileChange"
                    accept=".zip"
                    drag
                  >
                    <el-icon class="el-icon--upload"><Upload /></el-icon>
                    <div class="el-upload__text">
                      拖拽文件到此处或<em>点击上传</em>
                    </div>
                    <template #tip>
                      <div class="el-upload__tip">仅支持 .zip 文件</div>
                    </template>
                  </el-upload>
                </el-form-item>
                <el-form-item>
                  <el-button type="success" @click="uploadGroup" :disabled="!selectedGroupFile" :loading="uploadingGroup">
                    <el-icon><Upload /></el-icon>
                    上传并导入
                  </el-button>
                </el-form-item>
              </el-form>
              <el-alert type="info" :closable="false" style="margin-top: 10px;">
                导入群组将只导入群组配置，您需要手动创建群组并导入实例数据。
              </el-alert>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px;">
      <template #header>
        <span>实例数据说明（映射为容器内 /root）</span>
      </template>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="实例全量数据">包含配置、记忆、技能等容器内部 /root 下的所有文件</el-descriptions-item>
      </el-descriptions>
      <el-alert type="warning" :closable="false" style="margin-top: 15px;">
        导出实例时，将打包完整的实例数据目录。导入时，该目录将直接挂载为容器内部的 /root。
      </el-alert>
    </el-card>

    <OperationLog ref="operationLog" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { groupApi, instanceApi, systemApi } from '../api'
import OperationLog from '../components/OperationLog.vue'

const operationLog = ref(null)

const exportTab = ref('instance')
const importTab = ref('file')

const groups = ref([])
const instances = ref([])

const exportInstanceId = ref('')
const exportGroupId = ref('')
const importGroupId = ref('')
const importInstanceName = ref('')
const importSourceDir = ref('')
const importGroupIdDir = ref('')
const importInstanceNameDir = ref('')

const uploadRef = ref(null)
const groupUploadRef = ref(null)
const selectedFile = ref(null)
const selectedGroupFile = ref(null)
const uploading = ref(false)
const uploadingGroup = ref(false)

const loadGroups = async () => {
  try {
    groups.value = await groupApi.getAll()
  } catch (error) {
    ElMessage.error('获取群组失败')
  }
}

const loadInstances = async () => {
  try {
    instances.value = await instanceApi.getAll()
  } catch (error) {
    ElMessage.error('获取实例失败')
  }
}

const exportInstance = async () => {
  try {
    const result = await operationLog.value.execute('导出实例', async (addLog) => {
      addLog(`实例 ID: ${exportInstanceId.value}`, 'info')
      addLog('正在打包导出数据...', 'info')
      return await instanceApi.export(exportInstanceId.value)
    })
    ElMessage.success('实例导出成功')
    const downloadPath = result.export_path
    const fileName = downloadPath.split(/[/\\]/).pop()
    const downloadUrl = `/api/download?path=${encodeURIComponent(downloadPath)}`
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = fileName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } catch (error) {
    ElMessage.error('导出失败: ' + (typeof error === 'string' ? error : (error?.message || '未知错误')))
  }
}

const exportGroup = async () => {
  try {
    const result = await groupApi.export(exportGroupId.value)
    ElMessage.success('群组导出成功')
    const downloadPath = result.export_path
    const fileName = downloadPath.split(/[/\\]/).pop()
    const downloadUrl = `/api/download?path=${encodeURIComponent(downloadPath)}`
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = fileName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } catch (error) {
    ElMessage.error('导出失败: ' + (typeof error === 'string' ? error : (error?.message || '未知错误')))
  }
}

const handleFileChange = (uploadFile) => {
  selectedFile.value = uploadFile.raw
}

const uploadInstance = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请选择要上传的文件')
    return
  }
  uploading.value = true
  try {
    await operationLog.value.execute(`上传并导入实例: ${importInstanceName.value}`, async (addLog) => {
      addLog(`目标群组: ${importGroupId.value}`, 'info')
      addLog(`实例名称: ${importInstanceName.value}`, 'info')
      addLog('正在上传文件...', 'info')
      return await instanceApi.upload(importGroupId.value, importInstanceName.value, selectedFile.value)
    })
    ElMessage.success('实例上传导入成功')
    selectedFile.value = null
    importGroupId.value = ''
    importInstanceName.value = ''
    if (uploadRef.value) {
      uploadRef.value.clearFiles()
    }
    loadInstances()
  } catch (error) {
    ElMessage.error('上传导入失败: ' + (typeof error === 'string' ? error : (error?.message || '未知错误')))
  } finally {
    uploading.value = false
  }
}

const handleGroupFileChange = (uploadFile) => {
  selectedGroupFile.value = uploadFile.raw
}

const uploadGroup = async () => {
  if (!selectedGroupFile.value) {
    ElMessage.warning('请选择要上传的文件')
    return
  }
  uploadingGroup.value = true
  try {
    await groupApi.upload(selectedGroupFile.value)
    ElMessage.success('群组上传导入成功')
    selectedGroupFile.value = null
    if (groupUploadRef.value) {
      groupUploadRef.value.clearFiles()
    }
  } catch (error) {
    ElMessage.error('上传导入失败: ' + (typeof error === 'string' ? error : (error?.message || '未知错误')))
  } finally {
    uploadingGroup.value = false
  }
}

const importFromDirectory = async () => {
  try {
    const result = await instanceApi.importDirectory(importSourceDir.value, importGroupIdDir.value, importInstanceNameDir.value)
    ElMessage.success('从目录导入成功')
    importSourceDir.value = ''
    importGroupIdDir.value = ''
    importInstanceNameDir.value = ''
    loadInstances()
  } catch (error) {
    ElMessage.error('导入失败: ' + (typeof error === 'string' ? error : (error?.message || '未知错误')))
  }
}

const handleBrowse = async () => {
  try {
    const res = await systemApi.browseDirectory()
    if (res && res.path) {
      importSourceDir.value = res.path
    }
  } catch (error) {
    ElMessage.error('无法打开目录选择器: ' + error)
  }
}

const importGroup = async () => {
  try {
    const result = await groupApi.import(importGroupFile.value)
    ElMessage.success('群组导入成功: ' + result.message)
  } catch (error) {
    ElMessage.error('导入失败: ' + (typeof error === 'string' ? error : (error?.message || '未知错误')))
  }
}

onMounted(() => {
  loadGroups()
  loadInstances()
})
</script>

<style scoped>
.migration {
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
