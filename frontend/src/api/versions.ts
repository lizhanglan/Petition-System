import request from './request'

// 创建版本
export const createVersion = (data: {
  document_id: number
  content: string
  structured_content: any
  change_description?: string
}) => {
  return request.post('/versions/create', data)
}

// 获取版本列表
export const getVersionList = (documentId: number) => {
  return request.get(`/versions/list/${documentId}`)
}

// 获取版本详情
export const getVersionDetail = (versionId: number) => {
  return request.get(`/versions/${versionId}`)
}

// 版本对比
export const compareVersions = (data: {
  document_id: number
  version1: number
  version2: number
  compare_type?: string
}) => {
  return request.post('/versions/compare', {
    ...data,
    compare_type: data.compare_type || 'full'
  })
}

// 版本回滚
export const rollbackVersion = (data: {
  document_id: number
  target_version: number
  rollback_reason?: string
}) => {
  return request.post('/versions/rollback', data)
}
