import axios from 'axios'

const rawApi = axios.create({
  baseURL: '/curv/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

rawApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

rawApi.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error)
    if (error.response?.status === 401 || error.response?.status === 403) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (window.location.pathname !== '/curv/login') {
        window.location.href = '/curv/login'
      }
    }
    return Promise.reject(error)
  },
)

const api = {
  get: <T = any>(url: string, config?: any): Promise<T> => rawApi.get(url, config) as Promise<T>,
  post: <T = any>(url: string, data?: any, config?: any): Promise<T> => rawApi.post(url, data, config) as Promise<T>,
  put: <T = any>(url: string, data?: any, config?: any): Promise<T> => rawApi.put(url, data, config) as Promise<T>,
  delete: <T = any>(url: string, config?: any): Promise<T> => rawApi.delete(url, config) as Promise<T>,
}

export const authApi = {
  login: (username: string, password: string) =>
    rawApi.post<any, any>('/auth/login', new URLSearchParams({ username, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),
  getCurrentUser: () => api.get('/auth/me'),
}

export const dashboardApi = {
  getOverview: () => api.get('/dashboard'),
}

export const curvesApi = {
  // 曲线定义
  listDefinitions: (params?: any) => api.get('/curves/definitions', { params }),
  getDefinition: (code: string) => api.get(`/curves/definitions/${code}`),
  createDefinition: (data: any) => api.post('/curves/definitions', data),
  updateDefinition: (code: string, data: any) => api.put(`/curves/definitions/${code}`, data),
  deleteDefinition: (code: string) => api.delete(`/curves/definitions/${code}`),
  // 数据源/插件/派生/校验
  getDataSources: () => api.get('/curves/data-sources'),
  getPlugins: () => api.get('/curves/plugins'),
  getDerived: () => api.get('/curves/derived'),
  getRules: () => api.get('/curves/validation-rules'),
  // 曲线点定义
  listPoints: (params?: any) => api.get('/curves/points', { params }),
  createPoint: (data: any) => api.post('/curves/points', data),
  updatePoint: (id: number, data: any) => api.put(`/curves/points/${id}`, data),
  deletePoint: (id: number) => api.delete(`/curves/points/${id}`),
  batchPoints: (data: any) => api.post('/curves/points/batch', data),
}

export const collectionApi = {
  listRules: () => api.get('/collection/rules'),
  run: (data: any) => api.post('/collection/run', data),
  listLogs: (params?: any) => api.get('/collection/logs', { params }),
  listTasks: (params?: any) => api.get('/collection/tasks', { params }),
  listSources: () => api.get('/collection/sources'),
  getStats: () => api.get('/collection/stats'),
}

export const ratesApi = {
  query: (params: any) => api.get('/rates', { params }),
  getCurve: (code: string, date: string) => api.get(`/rates/curve/${code}/${date}`),
  import: (data: any) => api.post('/rates/import', data),
  // 曲线点 -> 利率历史（按日期维护）
  pointHistory: (curve_code: string, tenor: string) =>
    api.get('/rates/point-history', { params: { curve_code, tenor } }),
  pointBatch: (data: any) => api.post('/rates/point-batch', data),
  updateRate: (id: number, data: any) => api.put(`/rates/${id}`, data),
  deleteRate: (id: number) => api.delete(`/rates/${id}`),
}

export const buildApi = {
  splice: (data: any) => api.post('/build/splice', data),
  fit: (data: any) => api.post('/build/fit', data),
  interpolate: (data: any) => api.post('/build/interpolate', data),
}

export const analysisApi = {
  trend: (params: any) => api.get('/analysis/trend', { params }),
  spread: (params: any) => api.get('/analysis/spread', { params }),
  shapeMetrics: (params: any) => api.get('/analysis/shape-metrics', { params }),
  krd: (params: any) => api.get('/analysis/krd', { params }),
}

export const scenarioApi = {
  list: () => api.get('/scenario/list'),
  apply: (data: any) => api.post('/scenario/apply', data),
  run: (data: any) => api.post('/scenario/run', data),
}

export const agentApi = {
  chat: (data: any) => api.post('/agent/chat', data),
}

export const dictApi = {
  // 字典类型
  getTypes: (params?: any) => api.get('/dict/types', { params }),
  getType: (id: number) => api.get(`/dict/types/${id}`),
  createType: (data: any) => api.post('/dict/types', data),
  updateType: (id: number, data: any) => api.put(`/dict/types/${id}`, data),
  deleteType: (id: number) => api.delete(`/dict/types/${id}`),
  // 字典码值
  getData: (params?: any) => api.get('/dict/data', { params }),
  getAllData: () => api.get('/dict/data/all'),
  createData: (data: any) => api.post('/dict/data', data),
  updateData: (id: number, data: any) => api.put(`/dict/data/${id}`, data),
  deleteData: (id: number) => api.delete(`/dict/data/${id}`),
}

// 曲线点定义
export const curvePointsApi = {
  list: (params?: any) => api.get('/curves/points', { params }),
  create: (data: any) => api.post('/curves/points', data),
  update: (id: number, data: any) => api.put(`/curves/points/${id}`, data),
  delete: (id: number) => api.delete(`/curves/points/${id}`),
  batch: (data: any) => api.post('/curves/points/batch', data),
}

export default api