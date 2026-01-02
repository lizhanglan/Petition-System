import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, register as apiRegister, getCurrentUser } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<any>(null)

  const isAuthenticated = computed(() => !!token.value)

  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  const clearToken = () => {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  const login = async (username: string, password: string) => {
    const data = await apiLogin(username, password)
    setToken(data.access_token)
    await fetchUser()
  }

  const register = async (userData: any) => {
    await apiRegister(userData)
  }

  const logout = () => {
    clearToken()
  }

  const fetchUser = async () => {
    if (!token.value) return
    try {
      user.value = await getCurrentUser()
    } catch (error) {
      clearToken()
    }
  }

  return {
    token,
    user,
    isAuthenticated,
    login,
    register,
    logout,
    fetchUser
  }
})
