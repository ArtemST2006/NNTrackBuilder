<template>
  <section class="page dashboard">
    <div class="dashboard-left">
      <!-- 1. МАСТЕР СОЗДАНИЯ ЗАПРОСА -->
      <div class="card wizard-card">
        <h2 class="title">
          <span v-if="step === 1">Выберите, что вам интересно</span>
          <span v-else-if="step === 2">Сколько времени у вас есть?</span>
          <span v-else>Откуда начинаем прогулку?</span>
        </h2>

        <p class="subtitle" v-if="step === 1">Можно выбрать несколько вариантов</p>
        <p class="subtitle" v-else-if="step === 2">Введите число часов (например: 2.5)</p>
        <p class="subtitle" v-else>Выберите способ определения местоположения</p>

        <form class="form" @submit.prevent="onSubmit">
          <!-- Шаг 1 -->
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

          <!-- Шаг 2 -->
          <div v-else-if="step === 2">
            <div class="hint-box">
              <div class="hint-icon">💡</div>
              <div class="hint-text">Рекомендуем 2–4 часа для комфортной прогулки</div>
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

          <!-- Шаг 3 -->
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
                <div class="option-subtitle">Например: "Московский вокзал"</div>
              </button>
            </div>
            <label v-if="startMode === 'manual'" class="field" style="margin-top: 1rem">
              <span>Адрес (place)</span>
              <input
                v-model="place"
                type="text"
                placeholder='Например: "Нижегородский кремль"'
              />
            </label>
          </div>

          <p v-if="error" class="error-text">{{ error }}</p>
          <p v-if="message" class="success-text">{{ message }}</p>

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
            <button v-else type="submit" class="btn primary" :disabled="loading">
              Отправить запрос
            </button>
          </div>
        </form>
      </div>

      <!-- 2. СТАТИСТИКА / ИСТОРИЯ -->
      <div class="card stats-card">
        <div class="card-header">
          <h3 class="subtitle">История маршрутов</h3>
          <button class="btn-icon" @click="fetchStatistics" title="Обновить">🔄</button>
        </div>

        <div v-if="statsLoading" class="loading-text">Загрузка...</div>
        <div v-else-if="!statistics.length" class="empty-text">История пуста</div>

        <div v-else class="stats-list">
          <div v-for="stat in statistics" :key="stat.task_id" class="stat-item">
            <div class="stat-header">
              <span class="stat-date">{{ formatDate(stat.time) }}</span>
              <span class="stat-long">{{ stat.long }} км</span>
            </div>

            <div class="stat-desc">{{ stat.description }}</div>
            <div class="stat-advice">💡 {{ stat.advice }}</div>

            <details class="stat-details">
              <summary>Точки маршрута ({{ stat.output.length }})</summary>
              <ul class="places-list">
                <li v-for="(point, idx) in stat.output" :key="idx">
                  {{ point.description }}
                </li>
              </ul>
            </details>

            <button class="btn small outline full-width" @click="showOnMap(stat.output)">
              🗺 Показать на карте
            </button>
          </div>
        </div>
      </div>

      <!-- 3. WEBSOCKET STATUS -->
      <div class="card">
        <h3 class="subtitle">WebSocket статус</h3>
        <p>Подключение: <strong>{{ socketStatus }}</strong></p>
        <ul class="log">
          <li v-for="(msg, idx) in socketMessages" :key="idx">{{ msg }}</li>
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
import { storeToRefs } from 'pinia'
import { api } from '../services/http'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const auth = useAuthStore()
const { socketStatus, socketMessages } = storeToRefs(auth)

// --- Логика Wizard ---
const step = ref(1)
const category = ref([])
const customInterest = ref('')
const time = ref(3)
const place = ref('')
const cords = ref('')
const startMode = ref('geo')
const loading = ref(false)
const error = ref(null)
const message = ref(null)

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

const prevStep = () => { if (step.value > 1) step.value-- }

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

// --- Логика Статистики ---
const statistics = ref([])
const statsLoading = ref(false)

const fetchStatistics = async () => {
  if (!auth.user?.user_id) return
  statsLoading.value = true
  try {
    const resp = await api.get('/api/statistic', {
      params: { user_id: auth.user.user_id },
      headers: { Authorization: `Bearer ${auth.token}` }
    })

    statistics.value = resp.data.statistic || []
  } catch (e) {
    console.error('Ошибка получения статистики', e)
  } finally {
    statsLoading.value = false
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'
  }).format(date)
}

// --- Логика Карты ---
let mapInstance = null
let currentMarkers = []

const initMap = () => {
  mapInstance = L.map('map').setView([55.751244, 37.618423], 10)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
  }).addTo(mapInstance)
}

const showOnMap = (places) => {
  if (!mapInstance) return

  // Очищаем старые маркеры
  currentMarkers.forEach(m => mapInstance.removeLayer(m))
  currentMarkers = []

  if (!places || !places.length) return

  const bounds = []

  places.forEach(p => {
    // coordinates приходит строкой "lat, long"
    const [lat, lng] = p.coordinates.split(',').map(Number)
    if (!isNaN(lat) && !isNaN(lng)) {
      const marker = L.marker([lat, lng])
        .addTo(mapInstance)
        .bindPopup(p.description)

      currentMarkers.push(marker)
      bounds.push([lat, lng])
    }
  })

  if (bounds.length) {
    mapInstance.fitBounds(bounds, { padding: [50, 50] })
  }
}

// --- Логика Геолокации ---
const fillCoordsFromGeolocation = () =>
  new Promise((resolve) => {
    if (startMode.value !== 'geo' || !navigator.geolocation) {
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
    message.value = `Запрос принят. Ждем ответа... (Task: ${resp.data.task_id})`
  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  initMap()
  if (auth.isAuthenticated && auth.user?.user_id) {
    auth.connectWebSocket(auth.user.user_id)
    fetchStatistics() // Загружаем историю при входе
  }
})

onBeforeUnmount(() => {
  if (mapInstance) mapInstance.remove()
})
</script>

<style scoped>
/* Стили Wizard остались прежними (сокращено для читаемости) */
.wizard-card { max-width: 480px; }
.steps { display: flex; gap: 0.5rem; margin-bottom: 0.75rem; font-size: 0.8rem; color: #9ca3af; }
.step { padding: 0.25rem 0.5rem; border-radius: 999px; border: 1px solid transparent; }
.step.active { border-color: #3b82f6; color: #111827; }
.grid-options { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.5rem; }
.option-card { border-radius: 0.9rem; border: 1px solid #e5e7eb; background: white; padding: 0.6rem 0.7rem; display: flex; align-items: center; gap: 0.4rem; cursor: pointer; font-size: 0.9rem; }
.option-card.selected { border-color: #3b82f6; box-shadow: 0 4px 10px rgba(37, 99, 235, 0.25); }
.stack-options { display: flex; flex-direction: column; gap: 0.5rem; }
.hint-box { border-radius: 0.8rem; border: 1px solid #fee2e2; background: #fef2f2; padding: 0.5rem 0.7rem; display: flex; gap: 0.5rem; font-size: 0.85rem; }
.hint-text { color: #b91c1c; }
.actions-row { display: flex; justify-content: space-between; gap: 0.5rem; margin-top: 1rem; }

.dashboard {
  display: grid;
  grid-template-columns: 360px minmax(0, 1fr);
  gap: 1.5rem;
  height: calc(100vh - 80px);
  color: #000000; /* Глобальный черный цвет */
}

.dashboard-left {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow-y: auto;
  padding-right: 5px;
}

.dashboard-right {
  border-radius: 1rem;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.25);
  background: #f1f5f9; /* Светлый фон для карты, если карта не загрузится */
}

.map-container {
  width: 100%;
  height: 100%;
}

/* --- КАРТОЧКИ --- */
.card {
  background: #ffffff;
  border-radius: 1rem;
  padding: 1.5rem;
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  color: #000000; /* Чёрный текст внутри карточек */
}

.wizard-card {
  max-width: 480px;
}

/* --- ЗАГОЛОВКИ И ТЕКСТ --- */
.title {
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  color: #000000; /* Чёрный заголовок */
  line-height: 1.3;
}

.subtitle {
  color: #1a1a1a; /* Почти чёрный для подзаголовков */
  font-size: 0.95rem;
  margin-bottom: 1.5rem;
}

/* --- ШАГИ --- */
.steps {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  font-size: 0.8rem;
  color: #4b5563;
}

/* --- ОПЦИИ (КНОПКИ ВЫБОРА) --- */
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
  color: #000000; /* Чёрный текст в кнопках */
  transition: all 0.2s;
}

.option-card:hover {
  background: #f8fafc;
}

.option-card.selected {
  border-color: #000000;
  background: #f0f9ff;
  color: #000000;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.option-title {
  font-weight: 600;
}

.stack-options {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.option-card.wide {
  justify-content: flex-start;
}

.option-subtitle {
  font-size: 0.8rem;
  color: #444; /* Темно-серый для описания кнопок */
}

/* --- ПОЛЯ ВВОДА --- */
.field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.9rem;
  font-weight: 500;
  color: #000000;
}

input {
  padding: 0.6rem;
  border-radius: 0.5rem;
  border: 1px solid #cbd5e1;
  font-size: 1rem;
  color: #000000; /* Чёрный текст ввода */
  background: #fff;
}

input:focus {
  outline: none;
  border-color: #000000;
  box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.1);
}

/* --- ПОДСКАЗКИ И СООБЩЕНИЯ --- */
.hint-box {
  border-radius: 0.8rem;
  border: 1px solid #e0e7ff;
  background: #eef2ff;
  padding: 0.5rem 0.7rem;
  display: flex;
  gap: 0.5rem;
  font-size: 0.85rem;
  margin-bottom: 1rem;
}

.hint-text {
  color: #000000;
}

.error-text {
  color: #dc2626;
  font-size: 0.9rem;
  margin-top: 0.5rem;
  font-weight: 500;
}

.success-text {
  color: #16a34a;
  font-size: 0.9rem;
  margin-top: 0.5rem;
  font-weight: 500;
}

/* --- КНОПКИ ДЕЙСТВИЙ --- */
.actions-row {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  margin-top: 1.5rem;
}

.btn {
  padding: 0.6rem 1.2rem;
  border-radius: 0.5rem;
  border: none;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
  transition: opacity 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn.primary {
  background: #000000; /* Чёрная кнопка */
  color: white;
}

.btn.primary:hover:not(:disabled) {
  background: #333333;
}

.btn.outline {
  background: transparent;
  border: 1px solid #cbd5e1;
  color: #000000;
}

.btn.outline:hover:not(:disabled) {
  background: #f1f5f9;
}

/* --- СТАТИСТИКА (ИСТОРИЯ) --- */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.stats-card .subtitle {
  margin-bottom: 0;
  font-weight: 700;
  color: #000000;
}

.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.2rem;
}

.loading-text, .empty-text {
  text-align: center;
  color: #666;
  padding: 1rem;
}

.stats-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-height: 400px;
  overflow-y: auto;
}

.stat-item {
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  padding: 1rem;
  background: #ffffff; /* Белый фон */
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.stat-header {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: #333; /* Темно-серый для даты */
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.stat-desc {
  font-weight: 700;
  margin-bottom: 0.5rem;
  color: #000000; /* Чёрное название маршрута */
  font-size: 1rem;
}

.stat-advice {
  font-size: 0.9rem;
  color: #000000;
  background: #f3f4f6;
  padding: 0.5rem;
  border-radius: 0.4rem;
  margin-bottom: 0.8rem;
  border-left: 3px solid #000;
}

.stat-details {
  font-size: 0.9rem;
  margin-bottom: 0.8rem;
  color: #000000;
}

.places-list {
  padding-left: 1.2rem;
  margin-top: 0.5rem;
  color: #000000; /* Список мест чёрным */
  line-height: 1.5;
}

.full-width {
  width: 100%;
}

.small {
  padding: 0.4rem 0.5rem;
  font-size: 0.85rem;
}

/* --- ЛОГИ --- */
.log {
  max-height: 100px;
  overflow-y: auto;
  font-size: 0.75rem;
  font-family: monospace;
  background: #f1f5f9;
  padding: 0.5rem;
  border-radius: 0.5rem;
  color: #000;
}
</style>