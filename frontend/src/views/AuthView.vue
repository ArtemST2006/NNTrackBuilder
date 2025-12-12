<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

const mode = ref('login')
const email = ref('')
const username = ref('')          // <-- добавили
const password = ref('')
const confirmPassword = ref('')

const onSubmit = async () => {
  try {
    if (mode.value === 'login') {
      await auth.signIn(email.value, password.value)
      router.push({ name: 'dashboard' })
    } else {
      await auth.signUp(email.value, username.value, password.value, confirmPassword.value)
      mode.value = 'login'
    }
  } catch (e) {
    // ошибки уже выставлены в auth.error
  }
}
</script>

<template>
  <section class="page page-center">
    <div class="card card-md">
      <h2 class="title">Авторизация</h2>
      <div class="tabs">
        <button
          class="tab"
          :class="{ active: mode === 'login' }"
          @click="mode = 'login'"
        >
          Вход
        </button>
        <button
          class="tab"
          :class="{ active: mode === 'register' }"
          @click="mode = 'register'"
        >
          Регистрация
        </button>
      </div>

      <form class="form" @submit.prevent="onSubmit">
        <label class="field">
          <span>Email</span>
          <input v-model="email" type="email" required />
        </label>

        <!-- username только при регистрации -->
        <label v-if="mode === 'register'" class="field">
          <span>Имя пользователя</span>
          <input v-model="username" type="text" required />
        </label>

        <label class="field">
          <span>Пароль</span>
          <input v-model="password" type="password" required />
        </label>

        <label v-if="mode === 'register'" class="field">
          <span>Повторите пароль</span>
          <input v-model="confirmPassword" type="password" required />
        </label>

        <p v-if="auth.error" class="error-text">{{ auth.error }}</p>

        <button class="btn primary w-full" :disabled="auth.loading">
          {{ mode === 'login' ? 'Войти' : 'Зарегистрироваться' }}
        </button>
      </form>
    </div>
  </section>
</template>