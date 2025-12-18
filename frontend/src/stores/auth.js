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
    // ВХОД
    async signIn(email, password) {
      this.loading = true
      this.error = null
      try {
        const resp = await api.post('/api/sign-in', { email, password })
        const data = resp.data

        this.token = data.token
        this.user = { email: data.email, user_id: data.user_id }

        localStorage.setItem('token', this.token)
        localStorage.setItem('user', JSON.stringify(this.user))

        // Подключаем сокет после успешного входа
        this.connectWebSocket(data.user_id)
      } catch (err) {
        this.error = err.response?.data?.detail || 'Ошибка авторизации'
        throw err
      } finally {
        this.loading = false
      }
    },

    // РЕГИСТРАЦИЯ
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
      this.socket = new WebSocket(`ws://localhost:8000/ws/${userId}`)

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

      this.socket.onerror = () => {
        this.socketStatus = 'ошибка'
      }
    },

    // ВЫХОД
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