<template>
  <el-container class="app-container">
    <el-aside width="200px">
      <div class="logo">
        <h3>OpenClaw</h3>
        <p>Manager</p>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        class="side-menu"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/groups">
          <el-icon><Folder /></el-icon>
          <span>群组管理</span>
        </el-menu-item>
        <el-menu-item index="/instances">
          <el-icon><Box /></el-icon>
          <span>实例管理</span>
        </el-menu-item>
        <el-menu-item index="/config">
          <el-icon><Setting /></el-icon>
          <span>配置中心</span>
        </el-menu-item>
        <el-menu-item index="/migration">
          <el-icon><Upload /></el-icon>
          <span>数据迁移</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Tools /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-title">{{ pageTitle }}</div>
        <div class="header-actions">
          <el-button type="primary" @click="refreshData">
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const activeMenu = computed(() => route.path.split('/')[1] || '/dashboard')

const pageTitle = computed(() => {
  const titles = {
    '/dashboard': '仪表盘',
    '/groups': '群组管理',
    '/instances': '实例管理',
    '/config': '配置中心',
    '/migration': '数据迁移',
    '/settings': '系统设置'
  }
  return titles[route.path] || 'OpenClaw Manager'
})

const refreshData = () => {
  window.location.reload()
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.app-container {
  height: 100vh;
}

.el-aside {
  background: #1a1a2e;
  color: #fff;
}

.logo {
  padding: 20px;
  text-align: center;
  border-bottom: 1px solid #2d2d44;
}

.logo h3 {
  color: #409eff;
  margin-bottom: 5px;
}

.logo p {
  color: #888;
  font-size: 12px;
}

.side-menu {
  border-right: none;
  background: transparent;
}

.side-menu .el-menu-item {
  color: #ccc;
}

.side-menu .el-menu-item:hover,
.side-menu .el-menu-item.is-active {
  background: #16213e;
  color: #409eff;
}

.header {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid #eee;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.el-main {
  background: #f5f7fa;
  padding: 20px;
}
</style>
