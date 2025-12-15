<template>
  <div class="telegram-auth">
    <h2>🔗 Привязка Telegram аккаунта</h2>
    
    <div v-if="!isAuthenticated">
      <input v-model="email" placeholder="Email" type="email">
      <input v-model="password" placeholder="Пароль" type="password">
      <button @click="login">Войти</button>
      <button @click="signup">Регистрация</button>
    </div>
    
    <div v-else>
      <p>✅ Вы вошли как: {{ userEmail }}</p>
      <button @click="sendToBot">Отправить данные в бота</button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'

export default {
  setup() {
    const email = ref('')
    const password = ref('')
    const isAuthenticated = ref(false)
    const userEmail = ref('')
    const token = ref('')
    const userId = ref('')
    
    onMounted(() => {
      // Проверяем Telegram Web App
      if (window.Telegram?.WebApp) {
        const tg = window.Telegram.WebApp
        tg.expand()
        tg.ready()
      }
    })
    
    const login = async () => {
      try {
        const response = await axios.post('http://api-gateway:8000/api/sign-in', {
          email: email.value,
          password: password.value
        })
        
        token.value = response.data.token
        userId.value = response.data.user_id
        userEmail.value = email.value
        isAuthenticated.value = true
        
      } catch (error) {
        alert('Ошибка входа: ' + error.response?.data?.detail || error.message)
      }
    }
    
    const sendToBot = () => {
      if (window.Telegram?.WebApp) {
        const tg = window.Telegram.WebApp
        
        // Отправляем данные обратно в бота
        const data = {
          type: 'telegram_auth',
          token: token.value,
          user_id: userId.value,
          email: userEmail.value
        }
        
        tg.sendData(JSON.stringify(data))
        tg.close()
      }
    }
    
    return { email, password, isAuthenticated, userEmail, login, sendToBot }
  }
}
</script>