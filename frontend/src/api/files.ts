import request from './request'

export const uploadFile = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  
  return request.post('/files/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const getFileList = (skip: number = 0, limit: number = 20) => {
  return request.get('/files/list', { params: { skip, limit } })
}

export const getFilePreview = (fileId: number) => {
  return request.get(`/files/${fileId}/preview`)
}

export const deleteFile = (fileId: number) => {
  return request.delete(`/files/${fileId}`)
}
