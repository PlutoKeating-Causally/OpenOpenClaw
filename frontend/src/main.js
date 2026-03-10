import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import Dashboard from './views/Dashboard.vue'
import Groups from './views/Groups.vue'
import Instances from './views/Instances.vue'
import Config from './views/Config.vue'
import Migration from './views/Migration.vue'
import Settings from './views/Settings.vue'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', component: Dashboard },
  { path: '/groups', component: Groups },
  { path: '/instances', component: Instances },
  { path: '/instances/:groupId', component: Instances },
  { path: '/config', component: Config },
  { path: '/migration', component: Migration },
  { path: '/settings', component: Settings }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const app = createApp(App)
app.use(router)
app.use(ElementPlus)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.mount('#app')
