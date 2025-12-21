<template>
  <section class="page dashboard">
    <div class="dashboard-left">

      <!-- 1. РЕЗУЛЬТАТ (Показываем, если пришли данные по сокету) -->
      <div v-if="resultData" class="card result-card">
        <h2 class="title">{{ resultData.description }}</h2>
        <div class="subtitle">Маршрут готов!</div>

        <div class="stats-grid">
          <div class="stat-box">
            <span class="stat-label">Время</span>
            <span class="stat-value">{{ resultData.time }} ч.</span>
          </div>
          <div class="stat-box">
            <span class="stat-label">Расстояние</span>
            <span class="stat-value">{{ resultData.long }} км</span>
          </div>
        </div>

        <div class="advice-box">
          <div class="advice-icon">💡</div>
          <div class="advice-text">{{ resultData.advice }}</div>
        </div>

        <div class="route-list-title">Точки маршрута:</div>
        <ul class="route-list">
          <li v-for="(point, idx) in resultData.output" :key="idx" class="route-item">
            <span class="point-number">{{ idx + 1 }}.</span>
            <span class="point-desc">{{ point.description }}</span>
          </li>
        </ul>

        <button class="btn primary full-width" @click="resetToWizard">
          Вернуться к созданию
        </button>
      </div>

      <!-- 2. МАСТЕР СОЗДАНИЯ ЗАПРОСА (Скрываем, если есть результат) -->
      <div v-else class="card wizard-card">
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

      <!-- 3. СТАТИСТИКА / ИСТОРИЯ (Показываем только если не в режиме результата) -->
      <div v-if="!resultData" class="card stats-card">
        <div class="card-header">
          <h3 class="subtitle" style="margin:0">История маршрутов</h3>
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
            <!-- Кнопка "Показать на карте" теперь вызывает функцию для Яндекса -->
            <button class="btn small outline full-width" @click="drawRouteOnYandexMap(stat.output)">
              🗺 Показать на карте
            </button>
          </div>
        </div>
      </div>

       <!-- Логи вебсокета (для отладки) -->
       <div class="card" v-if="!resultData">
        <h3 class="subtitle" style="margin-bottom:0.5rem">WebSocket Debug</h3>
        <p style="font-size: 0.8rem">Status: <strong>{{ socketStatus }}</strong></p>
      </div>

    </div>

    <div class="dashboard-right">
      <!-- Контейнер для Яндекс Карты -->
      <div id="yandex-map" class="map-container"></div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref, watch, nextTick } from 'vue'
import { useAuthStore } from '../stores/auth'
import { storeToRefs } from 'pinia'
import { api } from '../services/http'
// Leaflet убрали, будем грузить Яндекс динамически

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
// Храним ID текущей задачи, чтобы поймать ответ
const currentTaskId = ref(null)
// Данные результата для отображения
const resultData = ref(null)

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

// Сброс к форме
const resetToWizard = () => {
  resultData.value = null
  step.value = 1
  message.value = null
  error.value = null
  currentTaskId.value = null
  // Очищаем карту
  if (mapInstance) {
    mapInstance.geoObjects.removeAll()
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

// --- Логика WebSocket Listener ---
// Следим за сообщениями в сторе
watch(socketMessages, (newMessages) => {
  if (!newMessages || newMessages.length === 0) return

  // Берем последнее сообщение
  const lastMsg = newMessages[newMessages.length - 1]

  // Если сообщение пришло как строка, парсим
  let data = lastMsg
  if (typeof lastMsg === 'string') {
    try {
      data = JSON.parse(lastMsg)
    } catch (e) {
      // Это может быть системное сообщение или не JSON
      return
    }
  }

  // Проверяем формат и task_id (если мы его ждем)
  // Либо если просто пришел результат с типом output (зависит от вашего протокола)
  if (data && data.task_id && data.output) {
    // Если это текущая задача или мы просто хотим показывать входящие результаты
    if (currentTaskId.value === data.task_id) {
       loading.value = false
       resultData.value = data // Переключаем экран
       message.value = 'Маршрут построен!'

       // Рисуем на карте (nextTick чтобы убедиться что DOM обновился, хотя карта в отдельном блоке)
       nextTick(() => {
         drawRouteOnYandexMap(data.output)
       })
    }
  }
}, { deep: true })


// --- Логика Яндекс Карт ---
let mapInstance = null

const initYandexMap = () => {
  ymaps.ready(() => {
    mapInstance = new ymaps.Map("yandex-map", {
      center: [56.326887, 44.005986], // Дефолт (Нижний Новгород)
      zoom: 12,
      controls: ['zoomControl', 'fullscreenControl']
    })
  })
}

// Функция отрисовки маршрута из ответа (JSON)
// Функция построения реального маршрута через Yandex MultiRouter
const drawRouteOnYandexMap = (places) => {
  if (!mapInstance || !window.ymaps) return

  // 1. Очищаем карту
  mapInstance.geoObjects.removeAll()

  // 2. Собираем только массив координат: [[56.1, 44.1], [56.2, 44.2], ...]
  // Это самый безопасный формат, который не вызывает ошибок
  const points = places.map(place =>
    place.coordinates.split(',').map(s => parseFloat(s.trim()))
  )

  // 3. Создаем маршрут
  const multiRoute = new ymaps.multiRouter.MultiRoute({
    referencePoints: points,
    params: {
      routingMode: 'pedestrian' // Пешеходный маршрут
    }
  }, {
    boundsAutoApply: true, // Автозум
    routeActiveStrokeColor: "#0000FF", // Цвет линии
    routeActiveStrokeWidth: 4
  })

  // 4. ВАЖНО: Добавляем подписи ПОСЛЕ того, как Яндекс обработает координаты
  multiRoute.model.events.add('requestsuccess', function() {
    // Получаем список точек маршрута (WayPoints)
    const wayPoints = multiRoute.getWayPoints();

    // Проходимся по всем точкам и проставляем описания из наших данных
    wayPoints.each((point, index) => {
      // Берем данные из исходного массива places по индексу
      const placeData = places[index];
      if (placeData) {
        point.properties.set({
          // Текст рядом с точкой (например: "1. Кремль")
          iconCaption: (index + 1) + ". " + placeData.description,
          // Текст внутри балуна при клике
          balloonContentHeader: placeData.description,
          balloonContentBody: placeData.description
        });
      }
    });
  });

  // 5. Добавляем на карту
  mapInstance.geoObjects.add(multiRoute)
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
    // 1. Если пользователь что-то печатал, но забыл нажать Enter — добавляем это сейчас
    if (customInterest.value.trim()) addCustomInterest()

    // 2. Получаем координаты
    await fillCoordsFromGeolocation()

    // 3. ФОРМИРУЕМ СПИСОК КАТЕГОРИЙ ДЛЯ ОТПРАВКИ
    let finalCategories = []

    // Проверяем, выбрана ли карточка "Все категории" (id: 'all')
    const isAllSelected = category.value.includes('all')

    if (isAllSelected) {
      // ЛОГИКА ДЛЯ "ВСЕ КАТЕГОРИИ":

      // А) Берем все стандартные варианты из interestOptions
      // Фильтруем, чтобы не брать саму кнопку "all"
      const standardLabels = interestOptions
        .filter(opt => opt.id !== 'all')
        .map(opt => opt.label) // <-- ВОТ ЗДЕСЬ БЕРЕТСЯ РУССКОЕ НАЗВАНИЕ (например "Кофейни")

      // Б) Ищем кастомные интересы, которые ввел пользователь (их нет в interestOptions)
      const customInputValues = category.value.filter(val =>
        val !== 'all' && !interestOptions.some(opt => opt.id === val)
      )

      // Объединяем: Все стандартные (на русском) + всё, что ввел юзер
      finalCategories = [...standardLabels, ...customInputValues]

    } else {
      // ЛОГИКА ОБЫЧНОГО ВЫБОРА:

      finalCategories = category.value.map(selectedId => {
        // Ищем объект опции, у которого id совпадает с тем, что выбрал юзер
        const option = interestOptions.find(opt => opt.id === selectedId)

        if (option) {
          // Если нашли (например id='cafes'), возвращаем label ('Кофейни')
          return option.label
        } else {
          // Если не нашли в списке (значит это ввел пользователь вручную), возвращаем как есть
          return selectedId
        }
      })
    }

    // Для отладки можно раскомментировать эту строку и посмотреть в консоль браузера перед отправкой
    // console.log('Отправляем на сервер:', finalCategories)

    const payload = {
      category: finalCategories, // Сюда уйдет массив ['Кофейни', 'Парки'] или ['Стрит-арт']
      time: time.value,
      cords: cords.value,
      place: place.value
    }

    const resp = await api.post('/api/predict', payload, {
      headers: { Authorization: `Bearer ${auth.token}` }
    })

    currentTaskId.value = resp.data.task_id
    message.value = `Запрос принят. Генерация маршрута...`

  } catch (err) {
    console.error(err)
    error.value = err.response?.data?.detail || 'Ошибка при отправке запроса'
    loading.value = false
  }
}

onMounted(() => {
  // Динамическая загрузка скрипта Яндекс Карт
  if (!window.ymaps) {
    const script = document.createElement('script')
    // Вставьте API KEY если есть, иначе оставьте пустым для dev-режима
    script.src = "https://api-maps.yandex.ru/2.1/?apikey=025b0277-5f19-4329-9ce5-76abf3790103&lang=ru_RU"
    script.onload = initYandexMap
    document.head.appendChild(script)
  } else {
    initYandexMap()
  }

  if (auth.isAuthenticated && auth.user?.user_id) {
    auth.connectWebSocket(auth.user.user_id)
    fetchStatistics()
  }
})

onBeforeUnmount(() => {
  if (mapInstance) {
    mapInstance.destroy()
  }
})
</script>

<style scoped>
/* Глобальные стили лэйаута */
.dashboard {
  display: grid;
  grid-template-columns: 360px minmax(0, 1fr);
  gap: 1.5rem;
  height: calc(100vh - 80px);
  color: #000000;
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
  background: #f1f5f9;
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
  color: #000000;
}

.wizard-card { max-width: 480px; }
.result-card { max-width: 480px; animation: fadeIn 0.3s ease-out; }

/* --- ЗАГОЛОВКИ --- */
.title {
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  color: #000000;
  line-height: 1.3;
}
.subtitle {
  color: #1a1a1a;
  font-size: 0.95rem;
  margin-bottom: 1.5rem;
}

/* --- Стили для RESULT CARD (Новые) --- */
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1.5rem;
}
.stat-box {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 0.8rem;
  padding: 0.8rem;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.stat-label { font-size: 0.8rem; color: #64748b; margin-bottom: 0.2rem; }
.stat-value { font-size: 1.1rem; font-weight: 700; color: #000; }

.advice-box {
  background: #eff6ff;
  border: 1px solid #dbeafe;
  border-radius: 0.8rem;
  padding: 1rem;
  display: flex;
  gap: 0.8rem;
  margin-bottom: 1.5rem;
  align-items: flex-start;
}
.advice-icon { font-size: 1.2rem; }
.advice-text { font-size: 0.9rem; line-height: 1.4; color: #1e3a8a; }

.route-list-title { font-weight: 700; margin-bottom: 0.5rem; }
.route-list {
  list-style: none;
  padding: 0;
  margin: 0 0 1.5rem 0;
}
.route-item {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  font-size: 0.95rem;
}
.point-number { font-weight: 600; color: #64748b; min-width: 20px; }
.full-width { width: 100%; margin-top: 1rem; }


/* --- ОСТАЛЬНЫЕ СТИЛИ (Из вашего кода) --- */
.steps { display: flex; gap: 0.5rem; margin-bottom: 0.75rem; font-size: 0.8rem; color: #4b5563; }
.grid-options { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.5rem; }
.option-card { border-radius: 0.9rem; border: 1px solid #e5e7eb; background: white; padding: 0.6rem 0.7rem; display: flex; align-items: center; gap: 0.4rem; cursor: pointer; font-size: 0.9rem; color: #000; transition: all 0.2s; }
.option-card:hover { background: #f8fafc; }
.option-card.selected { border-color: #000000; background: #f0f9ff; color: #000000; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1); }
.option-title { font-weight: 600; }
.stack-options { display: flex; flex-direction: column; gap: 0.5rem; }
.option-card.wide { justify-content: flex-start; }
.option-subtitle { font-size: 0.8rem; color: #444; }

.field { display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.9rem; font-weight: 500; color: #000; }
input { padding: 0.6rem; border-radius: 0.5rem; border: 1px solid #cbd5e1; font-size: 1rem; color: #000; background: #fff; }
input:focus { outline: none; border-color: #000; box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.1); }

.hint-box { border-radius: 0.8rem; border: 1px solid #e0e7ff; background: #eef2ff; padding: 0.5rem 0.7rem; display: flex; gap: 0.5rem; font-size: 0.85rem; margin-bottom: 1rem; }
.hint-text { color: #000; }
.error-text { color: #dc2626; font-size: 0.9rem; margin-top: 0.5rem; font-weight: 500; }
.success-text { color: #16a34a; font-size: 0.9rem; margin-top: 0.5rem; font-weight: 500; }

.actions-row { display: flex; justify-content: space-between; gap: 0.5rem; margin-top: 1.5rem; }
.btn { padding: 0.6rem 1.2rem; border-radius: 0.5rem; border: none; cursor: pointer; font-weight: 600; font-size: 0.9rem; transition: opacity 0.2s; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn.primary { background: #000; color: white; }
.btn.primary:hover:not(:disabled) { background: #333; }
.btn.outline { background: transparent; border: 1px solid #cbd5e1; color: #000; }
.btn.outline:hover:not(:disabled) { background: #f1f5f9; }

.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.btn-icon { background: none; border: none; cursor: pointer; font-size: 1.2rem; }
.loading-text, .empty-text { text-align: center; color: #666; padding: 1rem; }
.stats-list { display: flex; flex-direction: column; gap: 1rem; max-height: 400px; overflow-y: auto; }
.stat-item { border: 1px solid #e2e8f0; border-radius: 0.5rem; padding: 1rem; background: #fff; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
.stat-header { display: flex; justify-content: space-between; font-size: 0.85rem; color: #333; margin-bottom: 0.5rem; font-weight: 500; }
.stat-desc { font-weight: 700; margin-bottom: 0.5rem; color: #000; font-size: 1rem; }
.small { padding: 0.4rem 0.5rem; font-size: 0.85rem; }

@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>