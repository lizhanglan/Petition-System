import request, { longRequest } from './request'

// 上传并处理 Word 模板
export const uploadAndProcessTemplate = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)

  return longRequest.post('/templates/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// 确认保存模板
export const confirmTemplate = (data: {
  name: string
  document_type: string
  temp_template_path: string
  temp_original_path: string
  fields: Record<string, any>
}) => {
  return request.post('/templates/confirm', data)
}

// 获取模板列表
export const getTemplateList = (documentType?: string, skip: number = 0, limit: number = 50) => {
  return request.get('/templates/list', { params: { document_type: documentType, skip, limit } })
}

// 获取模板详情
export const getTemplate = (templateId: number) => {
  return request.get(`/templates/${templateId}`)
}

// 获取模板预览（下载模板文件）
export const getTemplatePreview = (templateId: number) => {
  return request.get(`/templates/${templateId}/preview`, {
    responseType: 'blob'
  })
}

// 删除模板
export const deleteTemplate = (templateId: number) => {
  return request.delete(`/templates/${templateId}`)
}

// ======== 旧版 API（兼容） ========

export const createTemplate = (data: any) => {
  return request.post('/templates/create', data)
}

// 使用长超时请求实例进行模板提取（AI操作需要更长时间）
export const extractTemplate = (fileId: number, autoSave: boolean = false) => {
  return longRequest.post('/templates/extract', { file_id: fileId, auto_save: autoSave })
}

export const saveExtractedTemplate = (data: any) => {
  return request.post('/templates/save-extracted', data)
}
