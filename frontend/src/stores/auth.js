import { defineStore } from 'pinia'
import { api } from '../services/http'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('user')) || null,
    token: localStorage.getItem('token') || null,
    loading: false,
    error: null,
    socket: null,
    socketStatus: 'отключено',
    socketMessages: []
  }),

  getters: {
    isAuthenticated: (state) => !!state.token
  },

  actions: {
    async signIn(email, password) {
      this.loading = true
      this.error = null
      try {
        // Убедитесь, что в ../services/http baseURL установлен в '/api' или пустой
        const resp = await api.post('/api/sign-in', { email, password })
        const data = resp.data

        this.token = data.token
        this.user = { email: data.email, user_id: data.user_id }

        localStorage.setItem('token', this.token)
        localStorage.setItem('user', JSON.stringify(this.user))

        this.connectWebSocket(data.user_id)
      } catch (err) {
        this.error = err.response?.data?.detail || 'Ошибка авторизации'
        throw err
      } finally {
        this.loading = false
      }
    },

    async signUp(email, username, password, confirmPassword) {
      this.loading = true
      this.error = null
      try {
        if (password !== confirmPassword) {
          throw new Error('Пароли не совпадают')
        }
        await api.post('/api/sign-up', {
          email,
          username,
          password
        })
      } catch (err) {
        this.error = err.response?.data?.detail || err.message || 'Ошибка регистрации'
        throw err
      } finally {
        this.loading = false
      }
    },

    connectWebSocket(userId) {
      if (this.socket?.readyState === 1) return

      this.socketStatus = 'подключение...'

      // ОПРЕДЕЛЯЕМ АДРЕС:
      // Если сайт на https, используем wss (secure websocket)
      // window.location.host автоматически подставит ваш IP (95.163.210.89)
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host; // это будет "95.163.210.89" (с портом 443 если https)

      // Используем проксирование через Vite (путь /ws)
      this.socket = new WebSocket(`${protocol}//${host}/ws/${userId}`)

      this.socket.onopen = () => {
        this.socketStatus = 'подключено'
        console.log('WS connected')
      }

      this.socket.onmessage = (event) => {
        const data = JSON.parse(event.data)
        this.socketMessages.push(JSON.stringify(data))
        console.log('WS data:', data)
      }

      this.socket.onclose = () => {
        this.socketStatus = 'отключено'
        this.socket = null
      }

      this.socket.onerror = (e) => {
        this.socketStatus = 'ошибка'
        console.error('WS Error:', e)
      }
    },

    logout() {
      this.user = null
      this.token = null
      this.error = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')

      if (this.socket) {
        this.socket.close()
        this.socket = null
        this.socketStatus = 'отключено'
        this.socketMessages = []
      }
    }
  }
})
