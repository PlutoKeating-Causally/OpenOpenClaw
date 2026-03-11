<template>
  <!-- Minimized floating badge -->
  <div v-if="hasContent && !expanded" class="log-badge" @click="expanded = true">
    <el-icon v-if="running" class="is-loading" :size="14"><Loading /></el-icon>
    <el-icon v-else-if="hasError" color="#f56c6c" :size="14"><CircleCloseFilled /></el-icon>
    <el-icon v-else color="#67c23a" :size="14"><CircleCheckFilled /></el-icon>
    <span class="badge-text">{{ title }}</span>
    <span class="badge-count">{{ logs.length }}</span>
  </div>

  <!-- Expanded floating panel -->
  <transition name="slide-up">
    <div v-if="hasContent && expanded" class="log-panel">
      <div class="log-panel-header">
        <div class="log-title">
          <el-icon v-if="running" class="is-loading"><Loading /></el-icon>
          <el-icon v-else-if="hasError" color="#f56c6c"><CircleCloseFilled /></el-icon>
          <el-icon v-else color="#67c23a"><CircleCheckFilled /></el-icon>
          <span>{{ title || '操作日志' }}</span>
        </div>
        <div class="log-actions">
          <el-button size="small" text style="color: #abb2bf;" @click="clearLogs" :disabled="running">清除</el-button>
          <el-button size="small" text style="color: #abb2bf;" @click="expanded = false" title="最小化">
            <el-icon><Minus /></el-icon>
          </el-button>
          <el-button size="small" text style="color: #abb2bf;" @click="closePanel" :disabled="running" title="关闭">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </div>
      <div class="log-container" ref="logContainer">
        <div v-for="(log, index) in logs" :key="index" :class="['log-line', log.type]">
          <span class="log-time">{{ log.time }}</span>
          <span class="log-prefix" v-if="log.type === 'cmd'">$</span>
          <span class="log-prefix" v-else-if="log.type === 'success'">✔</span>
          <span class="log-prefix" v-else-if="log.type === 'error'">✘</span>
          <span class="log-prefix" v-else-if="log.type === 'info'">ℹ</span>
          <span class="log-prefix" v-else>›</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
        <div v-if="running" class="log-line running">
          <span class="log-time">{{ currentTime() }}</span>
          <span class="log-prefix blink">▊</span>
          <span class="log-message">执行中...</span>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, nextTick, watch, computed } from 'vue'

const expanded = ref(false)
const running = ref(false)
const hasError = ref(false)
const title = ref('操作日志')
const logs = ref([])
const logContainer = ref(null)

const hasContent = computed(() => logs.value.length > 0 || running.value)

const currentTime = () => {
  const now = new Date()
  return now.toLocaleTimeString('zh-CN', { hour12: false })
}

const addLog = (message, type = 'info') => {
  logs.value.push({ message, type, time: currentTime() })
  scrollToBottom()
}

const scrollToBottom = () => {
  nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  })
}

const clearLogs = () => {
  logs.value = []
  hasError.value = false
}

const closePanel = () => {
  if (!running.value) {
    expanded.value = false
    logs.value = []
    hasError.value = false
  }
}

const execute = async (operationTitle, operationFn) => {
  title.value = operationTitle
  hasError.value = false
  running.value = true
  expanded.value = true

  addLog(`开始执行: ${operationTitle}`, 'cmd')

  try {
    const result = await operationFn(addLog)

    if (result && result.steps && Array.isArray(result.steps)) {
      for (const step of result.steps) {
        addLog(step.message || step, step.type || 'output')
      }
    }

    addLog(`${operationTitle} 完成`, 'success')
    running.value = false
    return result
  } catch (error) {
    const errorMsg = typeof error === 'string' ? error : (error?.message || error?.response?.data?.detail || '未知错误')
    addLog(`错误: ${errorMsg}`, 'error')
    hasError.value = true
    running.value = false
    throw error
  }
}

/**
 * Execute a streaming operation via SSE (Server-Sent Events).
 * @param {string} operationTitle - Title shown in the panel header.
 * @param {string} sseUrl - The SSE endpoint URL to connect to.
 * @returns {Promise<boolean>} true if success, false if error.
 */
const executeStream = (operationTitle, sseUrl) => {
  title.value = operationTitle
  hasError.value = false
  running.value = true
  expanded.value = true

  addLog(`开始执行: ${operationTitle}`, 'cmd')

  return new Promise((resolve, reject) => {
    fetch(sseUrl).then(response => {
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      function processStream() {
        reader.read().then(({ done, value }) => {
          if (done) {
            running.value = false
            if (hasError.value) {
              reject(new Error('Operation failed'))
            } else {
              addLog(`${operationTitle} 完成`, 'success')
              resolve(true)
            }
            return
          }

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() // Keep incomplete line in buffer

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const event = JSON.parse(line.substring(6))
                if (event.type === 'done') {
                  if (!event.success) {
                    hasError.value = true
                    addLog('操作失败', 'error')
                  }
                } else if (event.type === 'error') {
                  hasError.value = true
                  addLog(event.message, 'error')
                } else {
                  addLog(event.message, event.type || 'output')
                }
              } catch (e) {
                // Non-JSON line, just show it
                if (line.trim()) addLog(line, 'output')
              }
            }
          }

          processStream()
        }).catch(err => {
          addLog(`流连接错误: ${err.message}`, 'error')
          hasError.value = true
          running.value = false
          reject(err)
        })
      }

      processStream()
    }).catch(err => {
      addLog(`连接失败: ${err.message}`, 'error')
      hasError.value = true
      running.value = false
      reject(err)
    })
  })
}

watch(() => logs.value.length, () => {
  scrollToBottom()
})

defineExpose({ execute, executeStream, addLog, visible: expanded, running, clearLogs })
</script>

<style scoped>
/* Minimized badge */
.log-badge {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: #1a1a2e;
  color: #e0e0e0;
  padding: 8px 16px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  z-index: 2000;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
  border: 1px solid #333;
  transition: all 0.2s ease;
  font-size: 13px;
  max-width: 300px;
}

.log-badge:hover {
  background: #252545;
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.5);
}

.badge-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.badge-count {
  background: #404060;
  color: #abb2bf;
  padding: 1px 7px;
  border-radius: 10px;
  font-size: 11px;
  flex-shrink: 0;
}

/* Expanded panel */
.log-panel {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 40vh;
  background: #1a1a2e;
  z-index: 2000;
  display: flex;
  flex-direction: column;
  box-shadow: 0 -4px 30px rgba(0, 0, 0, 0.5);
  border-top: 1px solid #333;
}

.log-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: #16162a;
  border-bottom: 1px solid #2a2a4a;
  flex-shrink: 0;
}

.log-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #e0e0e0;
  font-size: 14px;
}

.log-actions {
  display: flex;
  gap: 2px;
}

.log-container {
  color: #e0e0e0;
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  padding: 12px 16px;
  flex: 1;
  overflow-y: auto;
  line-height: 1.8;
}

.log-line {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.log-time {
  color: #555;
  flex-shrink: 0;
  font-size: 11px;
  min-width: 70px;
}

.log-prefix {
  flex-shrink: 0;
  font-weight: bold;
  width: 16px;
  text-align: center;
}

.log-message {
  word-break: break-all;
}

.log-line.cmd .log-prefix { color: #61afef; }
.log-line.cmd .log-message { color: #61afef; }
.log-line.info .log-prefix { color: #abb2bf; }
.log-line.info .log-message { color: #abb2bf; }
.log-line.success .log-prefix { color: #98c379; }
.log-line.success .log-message { color: #98c379; }
.log-line.error .log-prefix { color: #e06c75; }
.log-line.error .log-message { color: #e06c75; }
.log-line.output .log-prefix { color: #d19a66; }
.log-line.output .log-message { color: #c8ccd4; }
.log-line.running .log-message { color: #e5c07b; }

.blink {
  animation: blink-animation 1s steps(2, start) infinite;
  color: #98c379;
}

@keyframes blink-animation {
  to { visibility: hidden; }
}

/* Slide animation */
.slide-up-enter-active, .slide-up-leave-active {
  transition: transform 0.3s ease;
}
.slide-up-enter-from, .slide-up-leave-to {
  transform: translateY(100%);
}
</style>
