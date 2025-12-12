// src/services/http.js
import axios from 'axios'

export const api = axios.create({
  baseURL: 'http://localhost:8000', // тут хост и порт api-gateway
})