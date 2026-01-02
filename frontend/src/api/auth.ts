import request from './request'

export const login = (username: string, password: string) => {
  const formData = new FormData()
  formData.append('username', username)
  formData.append('password', password)
  
  return request.post('/auth/login', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const register = (data: any) => {
  return request.post('/auth/register', data)
}

export const getCurrentUser = () => {
  return request.get('/auth/me')
}
