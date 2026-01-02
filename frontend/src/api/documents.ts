import request from './request'

// AI 研判需要更长的超时时间（2 分钟）
export const reviewDocument = (fileId: number) => {
  return request.post('/documents/review', { file_id: fileId }, {
    timeout: 120000 // 2 分钟
  })
}

export const generateDocument = (data: {
  template_id: number
  prompt: string
  context?: any[]
  session_id?: string
  file_references?: number[]
}) => {
  return request.post('/documents/generate', data, {
    timeout: 120000 // 2 分钟
  })
}

export const getDocumentList = (skip: number = 0, limit: number = 20) => {
  return request.get('/documents/list', { params: { skip, limit } })
}

export const getDocument = (documentId: number) => {
  return request.get(`/documents/${documentId}`)
}

// 对话管理 API
export const getConversationHistory = (sessionId?: string, limit?: number) => {
  return request.get('/documents/conversation/history', {
    params: { session_id: sessionId, limit }
  })
}

export const clearConversation = (sessionId?: string) => {
  return request.delete('/documents/conversation/clear', {
    params: { session_id: sessionId }
  })
}

export const getConversationInfo = (sessionId?: string) => {
  return request.get('/documents/conversation/info', {
    params: { session_id: sessionId }
  })
}

// 密级管理
export const updateClassification = (documentId: number, classification: string) => {
  return request.put(`/documents/${documentId}/classification`, { classification })
}

export const getClassifications = () => {
  return request.get('/documents/classifications')
}
