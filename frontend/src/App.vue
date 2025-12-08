<!-- 1. SCRIPT: Тут пишем логику (переменные, функции) -->
<script setup>
import { ref } from 'vue';

// --- Переменные (Состояние) ---
const email = ref('test_user') // Для теста сразу заполним
const prompt = ref('Нарисуй кота')
const userId = ref(null)       // Тут сохраним ID после входа
const taskId = ref(null)       // ID задачи от AI
const status = ref('Ожидание входа...')
const messages = ref([])       // История сообщений

// Адрес твоего API Gateway
const API_URL = 'http://localhost:8000';

// --- 1. Функция ВХОДА (HTTP) ---
const handleLogin = async () => {
  status.value = "Регистрация...";

  try {
    // Делаем POST запрос (как requests.post в Python)
    const res = await fetch(`${API_URL}/api/sign-up`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email.value,
        username: email.value, // Используем email как username для простоты
        password: "123"
      })
    });

    const data = await res.json();

    if (res.ok) {
      userId.value = data.user_id; // Запоминаем ID!
      status.value = `Вошли как ${userId.value}. Подключаем сокет...`;
      connectWebSocket(); // <--- Сразу открываем сокет
    } else {
      status.value = `Ошибка: ${data.detail}`;
    }
  } catch (e) {
    status.value = `Ошибка сети: ${e}`;
  }
}

// --- 2. Функция ВЕБСОКЕТА ---
let socket = null;

const connectWebSocket = () => {
  // Подключаемся к ws://localhost:8000/ws/{user_id}
  socket = new WebSocket(`ws://localhost:8000/ws/${userId.value}`);

  socket.onopen = () => {
    messages.value.push("🟢 WebSocket подключен!");
  };

  socket.onmessage = (event) => {
    // Когда пришло сообщение от Kafka через Gateway
    const data = JSON.parse(event.data);
    messages.value.push(`📩 Пришел ответ: ${JSON.stringify(data)}`);

    if (data.status === 'finished') {
       status.value = "Готово! Результат получен.";
    }
  };

  socket.onclose = () => {
    messages.value.push("🔴 WebSocket отключен");
  };
}

// --- 3. Функция ОТПРАВКИ ЗАДАЧИ (HTTP -> Kafka) ---
const sendTask = async () => {
  if (!userId.value) return alert("Сначала войдите!");

  status.value = "Отправляем задачу...";

  const res = await fetch(`${API_URL}/predict`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      // В будущем тут будет Authorization: Bearer TOKEN
    },
    body: JSON.stringify({
      prompt: prompt.value,
      params: {}
    })
  });

  const data = await res.json();
  taskId.value = data.task_id;
  messages.value.push(`📤 Задача ${data.task_id} отправлена в Kafka. Ждем...`);
}
</script>

<!-- 2. TEMPLATE: Тут верстка (HTML) -->
<template>
  <div class="container">
    <h1>AI Dashboard</h1>
    <p>Статус: <b>{{ status }}</b></p>

    <!-- Блок Входа -->
    <div class="box" v-if="!userId">
      <h3>Шаг 1: Вход</h3>
      <input v-model="email" placeholder="Username" />
      <button @click="handleLogin">Войти / Регистрация</button>
    </div>

    <!-- Блок Задач (появляется только если мы вошли) -->
    <div class="box" v-else>
      <h3>Шаг 2: Генерация</h3>
      <p>Вы вошли как: {{ userId }}</p>
      <input v-model="prompt" placeholder="Введите промпт..." />
      <button @click="sendTask" style="background: #3a86ff;">Отправить в AI</button>
    </div>

    <!-- Консоль сообщений -->
    <div class="logs">
      <div v-for="(msg, index) in messages" :key="index" class="log-item">
        {{ msg }}
      </div>
    </div>
  </div>
</template>

<!-- 3. STYLE: Тут красота (CSS) -->
<style scoped>
  .container { max-width: 500px; margin: 0 auto; font-family: sans-serif; }
  .box { display: flex; flex-direction: column; gap: 10px; padding: 20px; border: 1px solid #ddd; }
  input { padding: 10px; font-size: 16px; }
  button { padding: 10px; background: #42b883; color: white; border: none; cursor: pointer; }
  .logs { background: #f4f4f4; padding: 10px; margin-top: 20px; }
</style>