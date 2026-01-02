<template>
  <el-container class="layout-container">
    <el-aside width="200px">
      <div class="logo">信访文书系统</div>
      <el-menu
        :default-active="$route.path"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/dashboard">
          <span>工作台</span>
        </el-menu-item>
        <el-menu-item index="/files">
          <span>文件管理</span>
        </el-menu-item>
        <el-menu-item index="/documents">
          <span>文书管理</span>
        </el-menu-item>
        <el-menu-item index="/generate">
          <span>生成文书</span>
        </el-menu-item>
        <el-menu-item index="/templates">
          <span>模板管理</span>
        </el-menu-item>
        <el-menu-item index="/audit-logs">
          <span>审计日志</span>
        </el-menu-item>
        <el-sub-menu index="/system">
          <template #title>
            <span>系统管理</span>
          </template>
          <el-menu-item index="/system-health">
            <span>健康监控</span>
          </el-menu-item>
          <el-menu-item index="/rules-management">
            <span>规则管理</span>
          </el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header>
        <div class="header-content">
          <span>欢迎，{{ authStore.user?.username || '用户' }}</span>
          <el-button @click="handleLogout" text>退出登录</el-button>
        </div>
      </el-header>
      
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

onMounted(async () => {
  await authStore.fetchUser()
})

const handleLogout = () => {
  authStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.el-aside {
  background-color: #304156;
  color: #fff;
}

.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  font-size: 18px;
  font-weight: bold;
  color: #fff;
  background-color: #2b3a4a;
}

.el-header {
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  align-items: center;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.el-main {
  background-color: #f0f2f5;
  padding: 20px;
}
</style>
