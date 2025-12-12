<template>
  <section class="page dashboard">
    <div class="dashboard-left">
      <div class="card wizard-card">
        <!-- ШАПКА ВОПРОСА -->
        <h2 class="title">
          <span v-if="step === 1">Выберите, что вам интересно</span>
          <span v-else-if="step === 2">Сколько времени у вас есть?</span>
          <span v-else>Откуда начинаем прогулку?</span>
        </h2>

        <p class="subtitle" v-if="step === 1">
          Можно выбрать несколько вариантов
        </p>
        <p class="subtitle" v-else-if="step === 2">
          Введите число часов (например: 2.5)
        </p>
        <p class="subtitle" v-else>
          Выберите способ определения местоположения
        </p>

        <!-- СОДЕРЖИМОЕ ШАГОВ -->
        <form class="form" @submit.prevent="onSubmit">
          <!-- Шаг 1: интересы -->
          <div v-if="step === 1">
            <div class="grid-options">
              <button
                v-for="item in interestOptions"
                :key="item.id"
                type="button"
                class="option-card"
                :class="{ selected: category.includes(item.id) }"
                @click="toggleCategory(item.id)"
              >
                <div class="option-icon">{{ item.icon }}</div>
                <div class="option-title">{{ item.label }}</div>
              </button>
            </div>

            <label class="field" style="margin-top: 1rem">
              <span>Или введите свой интерес</span>
              <input
                v-model="customInterest"
                type="text"
                placeholder="Например: современное искусство"
                @keyup.enter="addCustomInterest"
              />
            </label>
          </div>

          <!-- Шаг 2: время -->
          <div v-else-if="step === 2">
            <div class="hint-box">
              <div class="hint-icon">💡</div>
              <div class="hint-text">
                Рекомендуем 2–4 часа для комфортной прогулки
              </div>
            </div>

            <label class="field" style="margin-top: 1rem">
              <span>Часы (time: float)</span>
              <input
                v-model.number="time"
                type="number"
                min="0.5"
                step="0.5"
                placeholder="Например: 3"
              />
            </label>
          </div>

          <!-- Шаг 3: старт -->
          <div v-else>
            <div class="stack-options">
              <button
                type="button"
                class="option-card wide"
                :class="{ selected: startMode === 'geo' }"
                @click="startMode = 'geo'"
              >
                <div class="option-icon large">📍</div>
                <div class="option-title">Отправить текущую геолокацию</div>
                <div class="option-subtitle">Рекомендуется</div>
              </button>

              <button
                type="button"
                class="option-card wide"
                :class="{ selected: startMode === 'manual' }"
                @click="startMode = 'manual'"
              >
                <div class="option-icon large">📝</div>
                <div class="option-title">Ввести адрес вручную</div>
                <div class="option-subtitle">
                  Например: "Московский вокзал"
                </div>
              </button>
            </div>

            <label
              v-if="startMode === 'manual'"
              class="field"
              style="margin-top: 1rem"
            >
              <span>Адрес (place)</span>
              <input
                v-model="place"
                type="text"
                placeholder='Например: "Нижегородский кремль"'
              />
            </label>
          </div>

          <!-- Сообщения -->
          <p v-if="error" class="error-text">{{ error }}</p>
          <p v-if="message" class="success-text">{{ message }}</p>

          <!-- КНОПКИ -->
          <div class="actions-row">
            <button
              type="button"
              class="btn outline"
              :disabled="loading || step === 1"
              @click="prevStep"
            >
              Назад
            </button>

            <button
              v-if="step < 3"
              type="button"
              class="btn primary"
              :disabled="loading"
              @click="nextStep"
            >
              Продолжить →
            </button>

            <button
              v-else
              type="submit"
              class="btn primary"
              :disabled="loading"
            >
              Отправить запрос
            </button>
          </div>
        </form>
      </div>

      <div class="card">
        <h3 class="subtitle">WebSocket статус</h3>
        <p>Подключение: {{ wsStatus }}</p>
        <ul class="log">
          <li v-for="(msg, idx) in wsMessages" :key="idx">
            {{ msg }}
          </li>
        </ul>
      </div>
    </div>

    <div class="dashboard-right">
      <div id="map" class="map-container"></div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { api } from '../services/http'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const auth = useAuthStore()

// шаг мастера
const step = ref(1)

// поля AIRequest
const category = ref([])       // list[str]
const customInterest = ref('')
const time = ref(3)            // float
const place = ref('')          // str
const cords = ref('')          // str (если берём геолокацию)
const startMode = ref('geo')   // 'geo' | 'manual'

// UI
const loading = ref(false)
const error = ref(null)
const message = ref(null)

// WS
const ws = ref(null)
const wsStatus = ref('отключено')
const wsMessages = ref([])

// карта
let mapInstance = null

const interestOptions = [
  { id: 'cafes', label: 'Кофейни', icon: '☕' },
  { id: 'street_art', label: 'Стрит-арт', icon: '🎨' },
  { id: 'museums', label: 'Музеи', icon: '🏛️' },
  { id: 'views', label: 'Панорамы', icon: '🌅' },
  { id: 'architecture', label: 'Архитектура', icon: '🏗️' },
  { id: 'parks', label: 'Парки', icon: '🌳' },
  { id: 'shops', label: 'Магазины', icon: '🛍️' },
  { id: 'all', label: 'Все категории', icon: '✨' }
]

// шаги
const nextStep = () => {
  if (step.value === 1 && !category.value.length && !customInterest.value) {
    error.value = 'Выберите интерес или введите свой'
    return
  }
  if (step.value === 2 && (!time.value || time.value <= 0)) {
    error.value = 'Введите корректное количество часов'
    return
  }
  error.value = null
  if (step.value < 3) step.value++
}

const prevStep = () => {
  if (step.value > 1) step.value--
}

// категории
const toggleCategory = (id) => {
  const idx = category.value.indexOf(id)
  if (idx >= 0) category.value.splice(idx, 1)
  else category.value.push(id)
}

const addCustomInterest = () => {
  const v = customInterest.value.trim()
  if (v) {
    category.value.push(v)
    customInterest.value = ''
  }
}

// карта
const initMap = () => {
  mapInstance = L.map('map').setView([55.751244, 37.618423], 10)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
  }).addTo(mapInstance)
  L.marker([55.751244, 37.618423]).addTo(mapInstance).bindPopup('Москва')
}

// WS
const connectWebSocket = () => {
  if (!auth.user?.user_id) {
    wsStatus.value = 'нет user_id'
    return
  }
  const url = `ws://${window.location.host}/ws/${auth.user.user_id}`
  ws.value = new WebSocket(url)

  ws.value.onopen = () => (wsStatus.value = 'подключено')
  ws.value.onclose = () => (wsStatus.value = 'отключено')
  ws.value.onerror = () => (wsStatus.value = 'ошибка')
  ws.value.onmessage = (event) => {
    wsMessages.value.push(event.data)
    // потом здесь можно будет парсить JSON и рисовать маршрут
  }
}

// геолокация -> cords
const fillCoordsFromGeolocation = () =>
  new Promise((resolve) => {
    if (startMode.value !== 'geo') {
      resolve()
      return
    }
    if (!navigator.geolocation) {
      resolve()
      return
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords
        cords.value = `${latitude},${longitude}`
        resolve()
      },
      () => resolve(),
      { enableHighAccuracy: true, timeout: 5000 }
    )
  })

// отправка AIRequest
const onSubmit = async () => {
  loading.value = true
  error.value = null
  message.value = null

  try {
    if (customInterest.value.trim()) addCustomInterest()
    await fillCoordsFromGeolocation()

    const payload = {
      category: category.value,
      time: time.value,
      cords: cords.value,
      place: place.value
    }

    const resp = await api.post('/api/predict', payload, {
      headers: { Authorization: `Bearer ${auth.token}` }
    })

    message.value = `Задача отправлена: task_id = ${resp.data.task_id}`
  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка при отправке запроса'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  initMap()
  connectWebSocket()
})

onBeforeUnmount(() => {
  if (ws.value) ws.value.close()
  if (mapInstance) mapInstance.remove()
})
</script>

<style scoped>
/* только то, что нужно для мастера */

.wizard-card {
  max-width: 480px;
}

/* шаги (упрощённая индикация) */
.steps {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  font-size: 0.8rem;
  color: #9ca3af;
}
.step {
  padding: 0.25rem 0.5rem;
  border-radius: 999px;
  border: 1px solid transparent;
}
.step.active {
  border-color: #3b82f6;
  color: #111827;
}

/* варианты интересов */
.grid-options {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.5rem;
}
.option-card {
  border-radius: 0.9rem;
  border: 1px solid #e5e7eb;
  background: white;
  padding: 0.6rem 0.7rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  cursor: pointer;
  font-size: 0.9rem;
}
.option-card.selected {
  border-color: #3b82f6;
  box-shadow: 0 4px 10px rgba(37, 99, 235, 0.25);
}
.option-icon {
  font-size: 1.1rem;
}
.option-title {
  font-weight: 500;
}

/* вертикальные опции */
.stack-options {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.option-card.wide {
  justify-content: flex-start;
}
.option-icon.large {
  font-size: 1.3rem;
}

/* подсказка */
.hint-box {
  border-radius: 0.8rem;
  border: 1px solid #fee2e2;
  background: #fef2f2;
  padding: 0.5rem 0.7rem;
  display: flex;
  gap: 0.5rem;
  font-size: 0.85rem;
}
.hint-text {
  color: #b91c1c;
}

/* кнопки */
.actions-row {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  margin-top: 1rem;
}

/* адаптация уже существующей разметки */
.dashboard {
  display: grid;
  grid-template-columns: 360px minmax(0, 1fr);
  gap: 1.5rem;
  height: calc(100vh - 80px);
}
.dashboard-left {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.dashboard-right {
  border-radius: 1rem;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.25);
  background: #020617;
}
.map-container {
  width: 100%;
  height: 100%;
}
</style>