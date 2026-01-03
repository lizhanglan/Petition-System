/**
 * ONLYOFFICE API
 */
import request from '../utils/request'

/**
 * 获取编辑器配置
 */
export const getEditorConfig = (fileId?: number, documentId?: number, mode: 'view' | 'edit' = 'view') => {
  return request.post('/onlyoffice/config', {
    file_id: fileId,
    document_id: documentId,
    mode
  })
}

/**
 * 检查ONLYOFFICE服务状态
 */
export const checkOnlyOfficeHealth = () => {
  return request.get('/onlyoffice/health')
}
