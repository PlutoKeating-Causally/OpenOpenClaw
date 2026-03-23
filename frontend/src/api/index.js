import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 300000  // 5 minutes default
})

api.interceptors.response.use(
  response => response.data,
  error => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    return Promise.reject(message)
  }
)

export const groupApi = {
  getAll: () => api.get('/groups'),
  getById: (id) => api.get(`/groups/${id}`),
  create: (data) => api.post('/groups', data),
  update: (id, data) => api.put(`/groups/${id}`, data),
  delete: (id) => api.delete(`/groups/${id}`),
  getConfig: (id) => api.get(`/groups/${id}/config`),
  updateConfig: (id, data) => api.put(`/groups/${id}/config`, data),
  export: (id) => api.post(`/groups/${id}/export`),
  upload: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/groups/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
}

export const instanceApi = {
  getAll: (groupId) => api.get('/instances', { params: { group_id: groupId } }),
  getById: (id) => api.get(`/instances/${id}`),
  create: (data) => api.post('/instances', data),
  delete: (id) => api.delete(`/instances/${id}`),
  start: (id) => api.post(`/instances/${id}/start`, null, { timeout: 600000 }),
  stop: (id) => api.post(`/instances/${id}/stop`),
  restart: (id) => api.post(`/instances/${id}/restart`),
  getLogs: (id, tail = 100) => api.get(`/instances/${id}/logs`, { params: { tail } }),
  getStats: (id) => api.get(`/instances/${id}/stats`),
  getConfig: (id) => api.get(`/instances/${id}/config`),
  updateConfig: (id, data) => api.put(`/instances/${id}/config`, data),
  batchStart: (ids) => api.post('/instances/batch/start', ids, { timeout: 1800000 }),
  batchStop: (ids) => api.post('/instances/batch/stop', ids),
  batchDelete: (ids) => api.post('/instances/batch/delete', ids),
  startAll: () => api.post('/instances/start-all'),
  stopAll: () => api.post('/instances/stop-all'),
  clone: (id, newName) => api.post(`/instances/${id}/clone`, null, { params: { new_name: newName } }),
  export: (id) => api.post(`/instances/${id}/export`),
  importDirectory: (sourceDir, groupId, name) => api.post('/instances/import-directory', { source_dir: sourceDir, group_id: groupId, name }),
  updatePorts: (id, data) => api.put(`/instances/${id}/ports`, data),
  getTerminal: (id) => api.get(`/instances/${id}/terminal`),
  upload: (groupId, name, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/instances/upload?group_id=${groupId}&name=${encodeURIComponent(name)}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
}

export const configApi = {
  getTemplates: () => api.get('/config/templates'),
  saveTemplates: (templates) => api.put('/config/templates', templates),
  getDefaults: (gatewayPort = 18789) => api.get('/config/defaults', { params: { gateway_port: gatewayPort } })
}

export const systemApi = {
  getStats: () => api.get('/system/stats'),
  getSettings: () => api.get('/system/settings'),
  updateSettings: (settings) => api.put('/system/settings', settings),
  pullImage: (image) => api.post('/system/pull-image', null, { params: { image }, timeout: 1800000 }),
  pullImageStreamUrl: (image) => `/api/system/pull-image-stream?image=${encodeURIComponent(image)}`,
  checkEnv: () => api.get('/system/env-check'),
  getNetworks: () => api.get('/system/networks'),
  getImages: () => api.get('/system/images'),
  browseDirectory: () => api.get('/system/browse-directory'),
  download: (path) => api.get('/download', { params: { path }, responseType: 'blob' })
}

export default api
