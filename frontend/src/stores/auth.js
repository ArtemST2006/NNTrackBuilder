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

    logout() {
      if (this.socket) {
        this.socket.close()
        this.socket = null
        this.socketStatus = 'отключено'
        this.socketMessages = []
      }
    }
  }
})