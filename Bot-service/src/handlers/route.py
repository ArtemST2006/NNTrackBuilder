import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

from states import RouteStates
from services.api_client import api_client
from services.token_storage import token_storage
from services.websocket_client import gateway_ws
from utils.keyboards import (
    get_interests_keyboard,
    get_time_keyboard,
    get_location_keyboard,
    get_main_menu_keyboard,
    get_cancel_keyboard
)

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("route"))
async def cmd_route(message: types.Message, state: FSMContext):
    """Начинаем создание маршрута - команда /route"""
    telegram_id = message.from_user.id
    
    # Проверяем авторизацию
    token = token_storage.get_token(telegram_id)
    user_id = token_storage.get_user_id(telegram_id)
    
    if not token:
        await message.answer(
            "🔐 <b>Требуется авторизация</b>\n\n"
            "Для создания персонализированных маршрутов нужно войти в аккаунт.\n\n"
            "Используйте команду /login или кнопку ниже.",
            reply_markup=get_main_menu_keyboard(is_authenticated=False)
        )
        return
    
    # Убеждаемся что WebSocket подключен
    if not gateway_ws.is_connected() or gateway_ws.user_id != user_id:
        await message.answer("🌐 Подключаюсь к сервису маршрутов...")
        connected = await gateway_ws.connect(user_id)
        if not connected:
            await message.answer(
                "❌ <b>Не удалось подключиться к сервису маршрутов</b>\n\n"
                "Попробуйте позже или обратитесь в поддержку.",
                reply_markup=get_main_menu_keyboard(is_authenticated=True)
            )
            return
    
    # Начинаем процесс создания маршрута
    await state.clear()
    await state.set_state(RouteStates.waiting_interests)
    
    await state.update_data(
        user_id=user_id,
        telegram_id=telegram_id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name or "",
        interests=[]
    )
    
    await message.answer(
        "🚀 <b>Начинаем создание маршрута!</b>\n\n"
        "🎯 <b>Шаг 1 из 3: Выбери что тебе интересно</b>\n"
        "<i>Можно выбрать несколько категорий, затем нажми '✅ Готово'</i>",
        reply_markup=get_interests_keyboard()
    )


@router.message(RouteStates.waiting_interests, F.text.in_([
    "☕ Кофейни", "🎨 Стрит-арт", "🏛️ Музеи", 
    "🌅 Панорамы", "🏛️ Архитектура", "🌳 Парки", "🛍️ Магазины"
]))
async def process_interest_selection(message: types.Message, state: FSMContext):
    """Пользователь выбрал интерес"""
    selected_interest = message.text
    
    # Получаем текущие данные
    data = await state.get_data()
    interests = data.get("interests", [])
    
    # Добавляем новый интерес
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
    
    # Переходим к следующему состоянию
    await state.set_state(RouteStates.waiting_time)
    
    interests_text = ", ".join(interests)
    
    await message.answer(
        f"🎯 <b>Отлично! Выбрано:</b> {interests_text}\n\n"
        "⏱️ <b>Шаг 2 из 3: Сколько времени у тебя есть?</b>\n"
        "<i>Выбери из предложенных или введи свое число (например: 2.5)</i>",
        reply_markup=get_time_keyboard()
    )


@router.message(RouteStates.waiting_time, F.text.in_(["1 час", "2 часа", "3 часа", "4 часа"]))
async def process_time_selection(message: types.Message, state: FSMContext):
    """Пользователь выбрал время из кнопок"""
    time_text = message.text
    
    # Извлекаем число из текста
    if time_text == "1 час":
        time_hours = 1.0
    elif time_text == "2 часа":
        time_hours = 2.0
    elif time_text == "3 часа":
        time_hours = 3.0
    elif time_text == "4 часа":
        time_hours = 4.0
    else:
        time_hours = 2.0  # fallback
    
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
        # Пробуем преобразовать в число
        time_hours = float(message.text.replace(',', '.'))
        
        # Проверяем диапазон
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


async def finish_route_creation(message: types.Message, state: FSMContext):
    """Завершаем сбор данных и создаем маршрут"""
    # Получаем все данные
    data = await state.get_data()
    
    await state.set_state(RouteStates.processing)
    
    # Формируем информацию о запросе
    interests = data.get("interests", [])
    time_hours = data.get("time_hours", 2.0)
    location = data.get("location", {})
    
    # Показываем пользователю что мы получили
    summary_text = f"""
📋 <b>Собранные данные:</b>

🎯 <b>Интересы:</b> {', '.join(interests) if interests else 'не выбрано'}
⏱️ <b>Время:</b> {time_hours} часов
📍 <b>Локация:</b> {location.get('text', 'не указана')}

🔄 <b>Создаю маршрут...</b>
<i>Это может занять несколько секунд</i>
"""
    
    await message.answer(summary_text, reply_markup=ReplyKeyboardRemove())
    
    # Отправляем запрос в API
    try:
        response = await api_client.create_route_request(
            telegram_id=message.from_user.id,
            categories=interests,
            time_hours=time_hours,
            location_data=location
        )
        
        if response["success"]:
            task_id = response["task_id"]
            
            # Ждем результат через WebSocket
            await message.answer("⏳ Ожидаю результат от AI Service...")
            
            result = await gateway_ws.wait_for_task(task_id, timeout=120)
            
            if result.get("status") == "finished":
                await show_real_route(message, result)
            else:
                await handle_route_error(message, result, data)
                
        else:
            await message.answer(
                f"❌ <b>Ошибка:</b> {response.get('error', 'Неизвестная ошибка')}\n\n"
                f"<i>Детали:</i> {response.get('details', 'Нет деталей')}",
                reply_markup=get_main_menu_keyboard(is_authenticated=True)
            )
            
    except Exception as e:
        logger.error(f"Ошибка при создании маршрута: {e}")
        await message.answer(
            "❌ <b>Внутренняя ошибка сервиса</b>\n\n"
            "Попробуйте позже или обратитесь в поддержку.",
            reply_markup=get_main_menu_keyboard(is_authenticated=True)
        )
    
    finally:
        await state.clear()


async def show_real_route(message: types.Message, result: dict):
    """Показать реальный маршрут из API"""
    route_data = result.get("payload", {}).get("route", [])
    
    if not route_data:
        await message.answer(
            "❌ Не удалось построить маршрут для указанных параметров\n\n"
            "Попробуйте изменить интересы или локацию.",
            reply_markup=get_main_menu_keyboard(is_authenticated=True)
        )
        return
    
    # Форматируем маршрут
    route_text = f"""
🗺️ <b>Ваш маршрут готов!</b>

🎯 <b>Всего точек:</b> {len(route_data)}
⏱️ <b>Общее время:</b> {sum(point.get('time', 30) for point in route_data) // 60} часов

<b>Маршрут включает:</b>
"""
    
    for i, point in enumerate(route_data, 1):
        name = point.get('name', f'Точка {i}')
        time_min = point.get('time', 30)
        description = point.get('description', '')
        
        route_text += f"\n{i}. <b>{name}</b> - {time_min} мин"
        if description:
            route_text += f"\n   <i>{description}</i>"
    
    route_text += "\n\n🚶 <b>Приятной прогулки!</b>"
    
    await message.answer(route_text, reply_markup=get_main_menu_keyboard(is_authenticated=True))


async def handle_route_error(message: types.Message, result: dict, original_data: dict):
    """Обработка ошибок при создании маршрута"""
    status = result.get("status")
    
    if status == "timeout":
        await message.answer(
            "⏳ <b>Маршрут все еще обрабатывается</b>\n\n"
            "AI Service долго обрабатывает ваш запрос.\n"
            "Мы пришлем уведомление когда он будет готов!",
            reply_markup=get_main_menu_keyboard(is_authenticated=True)
        )
    else:
        await message.answer(
            f"❌ <b>Ошибка при создании маршрута:</b> {result.get('error', 'Неизвестная ошибка')}\n\n"
            "Попробуйте изменить параметры и создать маршрут заново.",
            reply_markup=get_main_menu_keyboard(is_authenticated=True)
        )


@router.message(F.text == "❌ Отмена")
async def cancel_route(message: types.Message, state: FSMContext):
    """Отменить создание маршрута"""
    await state.clear()
    await message.answer(
        "❌ Создание маршрута отменено.",
        reply_markup=get_main_menu_keyboard(is_authenticated=True)
    )