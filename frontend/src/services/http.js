// src/services/http.js
import axios from 'axios'

export const api = axios.create({
  baseURL: '/api' // тут хост и порт api-gateway
})
