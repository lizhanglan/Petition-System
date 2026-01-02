import request from './request'

export const createTemplate = (data: any) => {
  return request.post('/templates/create', data)
}

export const getTemplateList = (documentType?: string, skip: number = 0, limit: number = 50) => {
  return request.get('/templates/list', { params: { document_type: documentType, skip, limit } })
}

export const getTemplate = (templateId: number) => {
  return request.get(`/templates/${templateId}`)
}
