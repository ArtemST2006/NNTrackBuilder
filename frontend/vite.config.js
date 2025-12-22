import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import basicSsl from '@vitejs/plugin-basic-ssl'

export default defineConfig({
  plugins: [vue(), basicSsl()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    https: true,
    proxy: {
      '/api': {
        target: 'http://api-gateway:8000',
        changeOrigin: true,
        rewrite: (path) => path
      },
      '/ws': {
        target: 'ws://api-gateway:8000', // перенаправляем на бэкенд
        ws: true, // ВАЖНО: включает проксирование веб-сокетов
        rewrite: (path) => path.replace(/^\/ws/, '/ws') // оставляем путь как есть
      }
    }
  }
})
