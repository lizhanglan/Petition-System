import request from './request'

// AI 研判需要更长的超时时间（2 分钟）
export const reviewDocument = (fileId: number) => {
  return request.post('/documents/review', { file_id: fileId }, {
    timeout: 120000 // 2 分钟
  })
}

export const generateDocument = (data: any) => {
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
