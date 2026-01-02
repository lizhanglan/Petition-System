import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const request = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 30000
})

// 创建一个用于长时间操作的请求实例（如AI处理）
export const longRequest = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 120000 // 120秒超时
})

// 为长请求实例添加拦截器
longRequest.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

longRequest.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      
      if (status === 401) {
        const authStore = useAuthStore()
        authStore.logout()
        window.location.href = '/login'
        ElMessage.error('登录已过期，请重新登录')
      } else {
        ElMessage.error(data.detail || '请求失败')
      }
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请稍后重试')
    } else {
      ElMessage.error('网络错误，请检查连接')
    }
    
    return Promise.reject(error)
  }
)

request.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

request.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      
      if (status === 401) {
        const authStore = useAuthStore()
        authStore.logout()
        window.location.href = '/login'
        ElMessage.error('登录已过期，请重新登录')
      } else {
        ElMessage.error(data.detail || '请求失败')
      }
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请稍后重试')
    } else {
      ElMessage.error('网络错误，请检查连接')
    }
    
    return Promise.reject(error)
  }
)

export default request
