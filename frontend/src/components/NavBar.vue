<template>
  <header class="navbar">
    <div class="navbar-left">
      <span class="navbar-logo">NNTrackBuilder</span>
    </div>
    <nav class="navbar-right">
      <RouterLink to="/" class="nav-link">Главная</RouterLink>
      <RouterLink v-if="!auth.isAuthenticated" to="/auth" class="nav-link">Вход</RouterLink>
      <RouterLink v-if="auth.isAuthenticated" to="/dashboard" class="nav-link">Дашборд</RouterLink>
      <button v-if="auth.isAuthenticated" class="nav-button" @click="logout">
        Выход
      </button>
    </nav>
  </header>
</template>

<script setup>
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

const logout = () => {
  auth.logout()
  router.push({ name: 'home' })
}
</script>
