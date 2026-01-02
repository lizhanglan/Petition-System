import request, { longRequest } from './request'

export const createTemplate = (data: any) => {
  return request.post('/templates/create', data)
}

export const getTemplateList = (documentType?: string, skip: number = 0, limit: number = 50) => {
  return request.get('/templates/list', { params: { document_type: documentType, skip, limit } })
}

export const getTemplate = (templateId: number) => {
  return request.get(`/templates/${templateId}`)
}

// 使用长超时请求实例进行模板提取（AI操作需要更长时间）
export const extractTemplate = (fileId: number, autoSave: boolean = false) => {
  return longRequest.post('/templates/extract', { file_id: fileId, auto_save: autoSave })
}

export const saveExtractedTemplate = (data: any) => {
  return request.post('/templates/save-extracted', data)
}
