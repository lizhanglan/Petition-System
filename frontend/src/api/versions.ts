import request from './request'

export const createVersion = (data: any) => {
  return request.post('/versions/create', data)
}

export const getVersionList = (documentId: number) => {
  return request.get(`/versions/list/${documentId}`)
}

export const rollbackVersion = (data: any) => {
  return request.post('/versions/rollback', data)
}
