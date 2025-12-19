<template>
  <div class="telegram-auth">
    <div class="container">
      <h2 class="title">🔗 Привязка Telegram аккаунта</h2>
      
      <div v-if="!isAuthenticated" class="auth-form">
        <div class="tabs">
          <button 
            @click="activeTab = 'login'"
            :class="{ active: activeTab === 'login' }"
          >
            Вход
          </button>
          <button 
            @click="activeTab = 'register'"
            :class="{ active: activeTab === 'register' }"
          >
            Регистрация
          </button>
        </div>
        
        <!-- Форма входа -->
        <div v-if="activeTab === 'login'" class="form-section">
          <div class="input-group">
            <label for="email">Email</label>
            <input 
              id="email"
              v-model="email" 
              placeholder="your@email.com" 
              type="email"
              @keyup.enter="login"
            >
          </div>
          
          <div class="input-group">
            <label for="password">Пароль</label>
            <input 
              id="password"
              v-model="password" 
              placeholder="••••••••" 
              type="password"
              @keyup.enter="login"
            >
          </div>
          
          <button @click="login" class="btn btn-primary" :disabled="loading">
            {{ loading ? 'Вход...' : 'Войти' }}
          </button>
        </div>
        
        <!-- Форма регистрации -->
        <div v-if="activeTab === 'register'" class="form-section">
          <div class="input-group">
            <label for="reg-email">Email</label>
            <input 
              id="reg-email"
              v-model="regEmail" 
              placeholder="your@email.com" 
              type="email"
            >
          </div>
          
          <div class="input-group">
            <label for="username">Имя пользователя</label>
            <input 
              id="username"
              v-model="username" 
              placeholder="Ваше имя" 
              type="text"
            >
          </div>
          
          <div class="input-group">
            <label for="reg-password">Пароль</label>
            <input 
              id="reg-password"
              v-model="regPassword" 
              placeholder="Не менее 6 символов" 
              type="password"
            >
          </div>
          
          <button @click="signup" class="btn btn-primary" :disabled="loading">
            {{ loading ? 'Регистрация...' : 'Зарегистрироваться' }}
          </button>
        </div>
        
        <div v-if="error" class="error-message">
          ❌ {{ error }}
        </div>
      </div>
      
      <div v-else class="success-screen">
        <div class="success-icon">✅</div>
        <h3>Успешная авторизация!</h3>
        <p>Вы вошли как: <strong>{{ userEmail }}</strong></p>
        
        <div class="user-info">
          <p>👤 <strong>ID:</strong> {{ userId }}</p>
          <p>🤖 <strong>Telegram ID:</strong> {{ telegramId }}</p>
        </div>
        
        <p class="instruction">
          Нажмите кнопку ниже чтобы отправить данные в бота.
          <br>
          <small>Окно закроется автоматически</small>
        </p>
        
        <button @click="sendToBot" class="btn btn-success">
          Отправить данные в бота
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

export default {
  name: 'TelegramAuth',
  
  setup() {
    // Состояние
    const activeTab = ref('login')
    const loading = ref(false)
    const error = ref('')
    
    // Данные для входа
    const email = ref('')
    const password = ref('')
    
    // Данные для регистрации
    const regEmail = ref('')
    const username = ref('')
    const regPassword = ref('')
    
    // Данные после успешной авторизации
    const isAuthenticated = ref(false)
    const userEmail = ref('')
    const token = ref('')
    const userId = ref('')
    const telegramId = ref('')
    
    // Telegram WebApp данные
    const initData = computed(() => {
      return window.Telegram?.WebApp?.initData || ''
    })
    
    onMounted(() => {
      // Инициализация Telegram WebApp
      if (window.Telegram?.WebApp) {
        const tg = window.Telegram.WebApp
        tg.expand()  // Развернуть на весь экран
        tg.ready()   // Сообщить Telegram что WebApp готов
        
        // Получаем Telegram ID пользователя
        if (tg.initDataUnsafe?.user?.id) {
          telegramId.value = tg.initDataUnsafe.user.id.toString()
        }
        
        console.log('Telegram WebApp инициализирован')
        console.log('Telegram ID:', telegramId.value)
        console.log('Init Data:', initData.value)
      } else {
        console.warn('Telegram WebApp не доступен')
        // Для разработки - тестовый Telegram ID
        telegramId.value = 'test_telegram_id'
      }
    })
    
    const login = async () => {
      if (!email.value || !password.value) {
        error.value = 'Заполните email и пароль'
        return
      }
      
      loading.value = true
      error.value = ''
      
      try {
        // Используем API Gateway (а не напрямую User-service)
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
        
        // 1. Вход пользователя
        const response = await axios.post(`${apiUrl}/api/sign-in`, {
          email: email.value,
          password: password.value
        })
        
        token.value = response.data.token
        userId.value = response.data.user_id
        userEmail.value = email.value
        
        // 2. Привязываем Telegram ID если он еще не привязан
        if (telegramId.value && !response.data.telegram_id) {
          try {
            await axios.post(`${apiUrl}/api/link_telegram`, {
              email: email.value,
              password: password.value,
              telegram_id: telegramId.value
            })
            
            console.log('✅ Telegram ID привязан')
          } catch (linkError) {
            console.warn('Не удалось привязать Telegram ID:', linkError.message)
          }
        }
        
        isAuthenticated.value = true
        
      } catch (err) {
        error.value = err.response?.data?.detail || 
                     err.response?.data?.error || 
                     'Ошибка подключения к серверу'
        console.error('Ошибка входа:', err)
      } finally {
        loading.value = false
      }
    }
    
    const signup = async () => {
      if (!regEmail.value || !username.value || !regPassword.value) {
        error.value = 'Заполните все поля'
        return
      }
      
      if (regPassword.value.length < 6) {
        error.value = 'Пароль должен быть не менее 6 символов'
        return
      }
      
      loading.value = true
      error.value = ''
      
      try {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
        
        // 1. Регистрация пользователя
        await axios.post(`${apiUrl}/api/sign-up`, {
          email: regEmail.value,
          username: username.value,
          password: regPassword.value
        })
        
        // 2. Автоматический вход после регистрации
        const loginResponse = await axios.post(`${apiUrl}/api/sign-in`, {
          email: regEmail.value,
          password: regPassword.value
        })
        
        token.value = loginResponse.data.token
        userId.value = loginResponse.data.user_id
        userEmail.value = regEmail.value
        
        // 3. Привязываем Telegram ID
        if (telegramId.value) {
          await axios.post(`${apiUrl}/api/link_telegram`, {
            email: regEmail.value,
            password: regPassword.value,
            telegram_id: telegramId.value
          })
          
          console.log('✅ Telegram ID привязан при регистрации')
        }
        
        isAuthenticated.value = true
        
      } catch (err) {
        error.value = err.response?.data?.detail || 
                     err.response?.data?.error || 
                     'Ошибка регистрации'
        console.error('Ошибка регистрации:', err)
      } finally {
        loading.value = false
      }
    }
    
    const sendToBot = () => {
      if (window.Telegram?.WebApp) {
        const tg = window.Telegram.WebApp
        
        // Данные для отправки в бота
        const data = {
          type: 'telegram_auth',
          token: token.value,
          user_id: userId.value,
          email: userEmail.value,
          telegram_id: telegramId.value,
          timestamp: Date.now()
        }
        
        console.log('Отправляем данные в бота:', data)
        
        // Отправляем данные обратно в бота
        tg.sendData(JSON.stringify(data))
        
        // Закрываем WebApp через секунду
        setTimeout(() => {
          tg.close()
        }, 1000)
        
      } else {
        console.error('Telegram WebApp не доступен для отправки данных')
        alert('Ошибка: WebApp недоступен')
      }
    }
    
    return {
      // Состояние
      activeTab,
      loading,
      error,
      
      // Данные для входа
      email,
      password,
      
      // Данные для регистрации
      regEmail,
      username,
      regPassword,
      
      // Результат
      isAuthenticated,
      userEmail,
      userId,
      telegramId,
      
      // Методы
      login,
      signup,
      sendToBot
    }
  }
}
</script>

<style scoped>
.telegram-auth {
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.container {
  background: white;
  border-radius: 20px;
  padding: 30px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.title {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
  font-size: 24px;
}

.tabs {
  display: flex;
  margin-bottom: 20px;
  border-bottom: 2px solid #eee;
}

.tabs button {
  flex: 1;
  padding: 12px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 16px;
  color: #666;
  transition: all 0.3s;
}

.tabs button.active {
  color: #667eea;
  border-bottom: 3px solid #667eea;
  font-weight: bold;
}

.form-section {
  margin-top: 20px;
}

.input-group {
  margin-bottom: 20px;
}

.input-group label {
  display: block;
  margin-bottom: 8px;
  color: #555;
  font-weight: 500;
}

.input-group input {
  width: 100%;
  padding: 12px 15px;
  border: 2px solid #ddd;
  border-radius: 10px;
  font-size: 16px;
  transition: border-color 0.3s;
}

.input-group input:focus {
  outline: none;
  border-color: #667eea;
}

.btn {
  width: 100%;
  padding: 14px;
  border: none;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  margin-top: 10px;
}

.btn-primary {
  background: linear-gradient(to right, #667eea, #764ba2);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 7px 14px rgba(102, 126, 234, 0.4);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-success {
  background: linear-gradient(to right, #4CAF50, #45a049);
  color: white;
}

.btn-success:hover {
  transform: translateY(-2px);
  box-shadow: 0 7px 14px rgba(76, 175, 80, 0.4);
}

.error-message {
  margin-top: 20px;
  padding: 12px;
  background: #ffebee;
  color: #c62828;
  border-radius: 8px;
  text-align: center;
}

.success-screen {
  text-align: center;
  padding: 20px 0;
}

.success-icon {
  font-size: 60px;
  margin-bottom: 20px;
  animation: success 0.6s ease;
}

@keyframes success {
  0% { transform: scale(0); }
  70% { transform: scale(1.2); }
  100% { transform: scale(1); }
}

.user-info {
  background: #f8f9fa;
  border-radius: 10px;
  padding: 15px;
  margin: 20px 0;
  text-align: left;
}

.user-info p {
  margin: 8px 0;
  color: #555;
}

.instruction {
  color: #666;
  margin: 20px 0;
  line-height: 1.5;
}

.instruction small {
  color: #999;
  font-size: 12px;
}
</style>