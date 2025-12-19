// src/services/http.js
import axios from 'axios'

export const api = axios.create({
  baseURL: 'http://95.163.210.89:8000', // тут хост и порт api-gateway
})
