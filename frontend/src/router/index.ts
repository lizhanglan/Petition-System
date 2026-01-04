import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue')
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/Register.vue')
    },
    {
      path: '/',
      name: 'Layout',
      component: () => import('@/views/Layout.vue'),
      redirect: '/dashboard',
      meta: { requiresAuth: true },
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/Dashboard.vue')
        },
        {
          path: 'files',
          name: 'Files',
          component: () => import('@/views/Files.vue')
        },
        {
          path: 'review/:fileId',
          name: 'Review',
          component: () => import('@/views/Review.vue')
        },
        {
          path: 'generate',
          name: 'Generate',
          component: () => import('@/views/Generate.vue')
        },
        {
          path: 'documents',
          name: 'Documents',
          component: () => import('@/views/Documents.vue')
        },
        {
          path: 'documents/:id/edit',
          name: 'DocumentEdit',
          component: () => import('@/views/DocumentEdit.vue')
        },
        {
          path: 'templates',
          name: 'Templates',
          component: () => import('@/views/Templates.vue')
        },
        {
          path: 'audit-logs',
          name: 'AuditLogs',
          component: () => import('@/views/AuditLogs.vue')
        },
        {
          path: 'system-health',
          name: 'SystemHealth',
          component: () => import('@/views/SystemHealth.vue')
        },
        {
          path: 'rules-management',
          name: 'RulesManagement',
          component: () => import('@/views/RulesManagement.vue')
        }
      ]
    }
  ]
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if ((to.path === '/login' || to.path === '/register') && authStore.isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

export default router
