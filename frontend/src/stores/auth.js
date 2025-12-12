import { defineStore } from 'pinia'
import { api } from '../services/http'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token') || null,
    loading: false,
    error: null
  }),
  getters: {
    isAuthenticated: (state) => !!state.token
  },
  actions: {
    async signIn(email, password) {
      this.loading = true
      this.error = null
      try {
        const resp = await api.post('/api/sign-in', { email, password })
        const data = resp.data
        this.token = data.token
        this.user = { email: data.email, user_id: data.user_id }
        localStorage.setItem('token', this.token)
      } catch (err) {
        this.error = err.response?.data?.detail || 'Ошибка авторизации'
        throw err
      } finally {
        this.loading = false
      }
    },

    // email, username, password, confirmPassword
    async signUp(email, username, password, confirmPassword) {
      this.loading = true
      this.error = null
      try {
        if (password !== confirmPassword) {
          throw new Error('Пароли не совпадают')
        }
        await api.post('/api/sign-up', {
          email,
          username,   // <-- важное поле
          password
        })
      } catch (err) {
        this.error = err.response?.data?.detail || err.message || 'Ошибка регистрации'
        throw err
      } finally {
        this.loading = false
      }
    },

    logout() {
      this.user = null
      this.token = null
      localStorage.removeItem('token')
    }
  }
})