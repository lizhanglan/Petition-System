import request from './request'

// 获取审计日志列表
export const getAuditLogList = (params: {
  page?: number
  page_size?: number
  action?: string
  resource_type?: string
  user_id?: number
  start_date?: string
  end_date?: string
  keyword?: string
}) => {
  return request.get('/audit-logs/list', { params })
}

// 获取审计日志统计
export const getAuditStats = (days: number = 7) => {
  return request.get('/audit-logs/stats', { params: { days } })
}

// 导出审计日志（返回完整URL）
export const exportAuditLogs = (params: {
  action?: string
  resource_type?: string
  start_date?: string
  end_date?: string
}) => {
  // 过滤掉空值
  const filteredParams: any = {}
  Object.entries(params).forEach(([key, value]) => {
    if (value) {
      filteredParams[key] = value
    }
  })
  
  const queryString = new URLSearchParams(filteredParams).toString()
  // 返回完整的后端 URL
  return `http://localhost:8000/api/v1/audit-logs/export${queryString ? '?' + queryString : ''}`
}

// 获取单条日志详情
export const getAuditLog = (logId: number) => {
  return request.get(`/audit-logs/${logId}`)
}
