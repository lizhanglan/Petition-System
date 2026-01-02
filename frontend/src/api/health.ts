import request from './request'

// 健康状态接口
export interface HealthStatus {
  status: string
  mode: string
  ai_service_available: boolean
  consecutive_failures: number
  consecutive_successes: number
  last_check_time: string
  fallback_start_time?: string
  estimated_recovery_time?: string
}

// 降级统计接口
export interface FallbackStats {
  total_checks: number
  total_failures: number
  total_fallback_events: number
  current_fallback_duration?: number
  average_fallback_duration?: number
  last_fallback_time?: string
}

// 获取健康状态
export const getHealthStatus = () => {
  return request.get<HealthStatus>('/health/status')
}

// 获取降级统计
export const getFallbackStats = () => {
  return request.get<FallbackStats>('/health/fallback-stats')
}

// 简单健康检查
export const healthCheck = () => {
  return request.get('/health/check')
}
