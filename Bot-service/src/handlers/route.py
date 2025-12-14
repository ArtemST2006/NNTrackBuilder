from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

from states import RouteStates
from utils.keyboards import get_interests_keyboard, get_time_keyboard, get_location_keyboard

router = Router()

# ========== ГЛАВНЫЙ ОБРАБОТЧИК КОМАНДЫ /route ==========

@router.message(Command("route"))
async def cmd_route(message: types.Message, state: FSMContext):
    """Начинаем создание маршрута - команда /route"""
    await state.clear()
    
    await state.set_state(RouteStates.waiting_interests)
    
    await state.update_data(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        interests=[]
    )
    
    await message.answer(
        "🚀 <b>Начинаем создание маршрута!</b>\n\n"
        "🎯 <b>Шаг 1 из 3: Выбери что тебе интересно</b>\n"
        "<i>Можно выбрать несколько категорий, затем нажми '✅ Готово'</i>",
        reply_markup=get_interests_keyboard()
    )

# ========== СОСТОЯНИЕ 1: ВЫБОР ИНТЕРЕСОВ ==========

@router.message(RouteStates.waiting_interests, F.text.in_([
    "☕ Кофейни", "🎨 Стрит-арт", "🏛️ Музеи", 
    "🌅 Панорамы", "🏛️ Архитектура", "🌳 Парки", "🛍️ Магазины"
]))
async def process_interest_selection(message: types.Message, state: FSMContext):
    """Пользователь выбрал интерес"""
    selected_interest = message.text
    
    data = await state.get_data()
    interests = data.get("interests", [])
    
    interests.append(selected_interest)
    await state.update_data(interests=interests)
    
    await message.answer(f"✅ Добавлено: {selected_interest}")


@router.message(RouteStates.waiting_interests, F.text == "✅ Готово")
async def process_interests_done(message: types.Message, state: FSMContext):
    """Пользователь закончил выбирать интересы"""
    data = await state.get_data()
    interests = data.get("interests", [])
    
    if not interests:
        await message.answer(
            "❌ Нужно выбрать хотя бы одну категорию!\n"
            "Попробуй еще раз:",
            reply_markup=get_interests_keyboard()
        )
        return
    
    await state.set_state(RouteStates.waiting_time)
    
    interests_text = ", ".join(interests)
    
    await message.answer(
        f"🎯 <b>Отлично! Выбрано:</b> {interests_text}\n\n"
        "⏱️ <b>Шаг 2 из 3: Сколько времени у тебя есть?</b>\n"
        "<i>Выбери из предложенных или введи свое число (например: 2.5)</i>",
        reply_markup=get_time_keyboard()
    )


# ========== СОСТОЯНИЕ 2: ВВОД ВРЕМЕНИ ==========

@router.message(RouteStates.waiting_time, F.text.in_(["1 час", "2 часа", "3 часа", "4 часа"]))
async def process_time_selection(message: types.Message, state: FSMContext):
    """Пользователь выбрал время из кнопок"""
    time_text = message.text
    if time_text == "1 час":
        time_hours = 1.0
    elif time_text == "2 часа":
        time_hours = 2.0
    elif time_text == "3 часа":
        time_hours = 3.0
    elif time_text == "4 часа":
        time_hours = 4.0
    else:
        time_hours = 2.0  
    
    await process_time_value(message, state, time_hours)


@router.message(RouteStates.waiting_time, F.text == "Другое время...")
async def process_custom_time_request(message: types.Message, state: FSMContext):
    """Пользователь хочет ввести свое время"""
    await message.answer(
        "⏱️ <b>Введи количество часов:</b>\n"
        "<i>Например: 1.5 или 2.75</i>\n"
        "<i>Минимум: 0.5 часа, максимум: 8 часов</i>",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(RouteStates.waiting_time)
async def process_time_input(message: types.Message, state: FSMContext):
    """Пользователь ввел время вручную"""
    try:
        time_hours = float(message.text.replace(',', '.'))
        
        if 0.5 <= time_hours <= 8:
            await process_time_value(message, state, time_hours)
        else:
            await message.answer(
                "❌ Время должно быть от 0.5 до 8 часов.\n"
                "Попробуй еще раз:"
            )
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введи число.\n"
            "Например: 2.5 или 3"
        )


async def process_time_value(message: types.Message, state: FSMContext, time_hours: float):
    """Обработка числового значения времени"""
    await state.update_data(time_hours=time_hours)
    await state.set_state(RouteStates.waiting_location)
    
    await message.answer(
        f"⏱️ <b>Отлично! Время:</b> {time_hours} часов\n\n"
        "📍 <b>Шаг 3 из 3: Откуда начинаем прогулку?</b>\n"
        "<i>Отправь геолокацию или введи адрес</i>",
        reply_markup=get_location_keyboard()
    )


# ========== СОСТОЯНИЕ 3: ПОЛУЧЕНИЕ ЛОКАЦИИ ==========

@router.message(RouteStates.waiting_location, F.text == "🏙️ Ввести адрес")
async def process_address_request(message: types.Message, state: FSMContext):
    """Пользователь хочет ввести адрес"""
    await message.answer(
        "🏙️ <b>Введи адрес или название места:</b>\n"
        "<i>Например: Нижегородский кремль, ул. Большая Покровская</i>",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(RouteStates.waiting_location, F.location)
async def process_location(message: types.Message, state: FSMContext):
    """Пользователь отправил геолокацию"""
    location = message.location
    
    await state.update_data(
        location={
            "type": "coordinates",
            "lat": location.latitude,
            "lon": location.longitude,
            "text": "геолокация"
        }
    )
    
    await finish_route_creation(message, state)


@router.message(RouteStates.waiting_location)
async def process_address_input(message: types.Message, state: FSMContext):
    """Пользователь ввел адрес"""
    address = message.text
    
    await state.update_data(
        location={
            "type": "address",
            "text": address,
            "lat": None,
            "lon": None
        }
    )
    
    await finish_route_creation(message, state)


# ========== ЗАВЕРШЕНИЕ СОЗДАНИЯ МАРШРУТА ==========

async def finish_route_creation(message: types.Message, state: FSMContext):
    """Завершаем сбор данных и создаем маршрут"""
    data = await state.get_data()
    
    await state.set_state(RouteStates.processing)
    
    interests = data.get("interests", [])
    time_hours = data.get("time_hours", 2.0)
    location = data.get("location", {})
    
    summary_text = f"""
📋 <b>Собранные данные:</b>

🎯 <b>Интересы:</b> {', '.join(interests) if interests else 'не выбрано'}
⏱️ <b>Время:</b> {time_hours} часов
📍 <b>Локация:</b> {location.get('text', 'не указана')}

🔄 <b>Создаю маршрут...</b>
<i>Это может занять несколько секунд</i>
"""
    
    await message.answer(summary_text, reply_markup=ReplyKeyboardRemove())
    
    # Показываем демо-результат (пока нет интеграции с API)
    await show_demo_route(message, data)
    
    # Очищаем состояние
    await state.clear()


async def show_demo_route(message: types.Message, data: dict):
    """Показываем демо-маршрут (временное решение)"""
    interests = data.get("interests", ["разные места"])
    time_hours = data.get("time_hours", 2.0)
    location_text = data.get("location", {}).get("text", "геолокация")
    
    # Генерируем демо-маршрут на основе интересов
    demo_points = []
    if "☕ Кофейни" in interests:
        demo_points.append("☕ Кафе 'Хлебная лавка' (40 мин)")
    if "🎨 Стрит-арт" in interests:
        demo_points.append("🎨 Граффити 'Нижегородские тигры' (30 мин)")
    if "🏛️ Музеи" in interests:
        demo_points.append("🏛️ Нижегородский Кремль (60 мин)")
    if "🌅 Панорамы" in interests:
        demo_points.append("🌅 Чкаловская лестница (45 мин)")
    if "🏛️ Архитектура" in interests:
        demo_points.append("🏛️ Усадьба Рукавишниковых (50 мин)")
    if "🌳 Парки" in interests:
        demo_points.append("🌳 Парк Швейцария (60 мин)")
    if "🛍️ Магазины" in interests:
        demo_points.append("🛍️ ТЦ 'Небо' (60 мин)")
    
    # Если ничего не выбрано, добавляем общие места
    if not demo_points:
        demo_points = [
            "📍 Нижегородский Кремль (60 мин)",
            "📍 Большая Покровская улица (45 мин)",
            "📍 Чкаловская лестница (30 мин)"
        ]
    
    # Ограничиваем количество точек по времени
    max_points = min(int(time_hours * 60 / 30), 5)  # ~30 мин на точку
    demo_points = demo_points[:max_points]
    
    route_text = f"""
🗺️ <b>ДЕМО-МАРШРУТ</b>

🎯 <b>Интересы:</b> {', '.join(interests) if interests else 'разные места'}
⏱️ <b>Время:</b> {time_hours} часов
📍 <b>Старт:</b> {location_text}

<b>Маршрут включает:</b>
{chr(10).join(f'• {point}' for point in demo_points)}

✅ <b>Всего точек:</b> {len(demo_points)}
🚶 <b>Примерная дистанция:</b> {time_hours * 1.2:.1f} км

💡 <i>Это демо-версия. Реальные маршруты будут после запуска AI Service!</i>

🔄 Хочешь попробовать еще? Используй /route
"""
    
    await message.answer(route_text)
    