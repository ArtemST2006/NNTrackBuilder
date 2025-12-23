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
)

router = Router()
logger = logging.getLogger(__name__)

INTERESTS_MAP = {
    "☕ Кофейни": "кофейни",
    "🎨 Искусство": "искусство",
    "🏛️ Музей": "музей",
    "🌅 С детьми": "С детьми",
    "🏛️ Архитектура": "архитектура",
    "🌳 Парки": "парки",
    "🛍️ Магазины": "магазины",
}
PRESET_INTERESTS = set(INTERESTS_MAP.keys())

# ------------------- Парсим координаты ---------------------

from urllib.parse import quote
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def _parse_coords(s: str):
    # "55.7558, 37.6173" -> (55.7558, 37.6173)
    try:
        parts = [p.strip() for p in (s or "").split(",")]
        if len(parts) != 2:
            return None
        lat = float(parts[0])
        lon = float(parts[1])
        return lat, lon
    except Exception:
        return None

def _build_yandex_route_url(output: list[dict], mode: str = "pd") -> str | None:
    coords = []
    for p in output:
        parsed = _parse_coords(p.get("coordinates", ""))
        if parsed:
            lat, lon = parsed
            coords.append(f"{lat},{lon}")

    # Для маршрута нужно минимум 2 точки
    if len(coords) < 2:
        return None

    rtext = "~".join(coords)
    return f"https://yandex.ru/maps/?rtext={quote(rtext)}&rtt={mode}"


# --------------- Старт -------------------

@router.message(Command("route"))
async def cmd_route(message: types.Message, state: FSMContext):
    logger.info("start route. version 1")
    """Начинаем создание маршрута - команда /route"""
    telegram_id = message.from_user.id

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

    await state.clear()
    await state.set_state(RouteStates.waiting_interests)

    await state.update_data(
        user_id=user_id,
        telegram_id=telegram_id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name or "",
        interests=[],        
        interests_ui=[] 
    )

    await message.answer(
        "🚀 <b>Начинаем создание маршрута!</b>\n\n"
        "🎯 <b>Шаг 1 из 3: Выбери что тебе интересно</b>\n"
        "<i>Можно выбрать несколько категорий, затем нажми '✅ Готово'</i>\n"
        "<i>Также можно вводить интересы вручную текстом</i>",
        reply_markup=get_interests_keyboard()
    )


# ---------- ИНТЕРЕСЫ (кнопки + ручной ввод) ----------

@router.message(RouteStates.waiting_interests, F.text == "✏️ Ввести свои варианты")
async def process_custom_interests_request(message: types.Message, state: FSMContext):
    logger.info("process_custom_interests_request")
    await message.answer(
        "✏️ <b>Введи интересы вручную</b>\n"
        "<i>Можно несколько через запятую или с новой строки.</i>\n"
        "Например: кофе, бары, видовые площадки",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(RouteStates.waiting_interests, F.text == "✅ Готово")
async def process_interests_done(message: types.Message, state: FSMContext):
    logger.info("process_interests_done")
    """Пользователь закончил выбирать интересы"""
    data = await state.get_data()
    interests = data.get("interests", [])
    interests_ui = data.get("interests_ui", [])

    if not interests:
        await message.answer(
            "❌ Нужно выбрать хотя бы одну категорию!\n"
            "Попробуй еще раз:",
            reply_markup=get_interests_keyboard()
        )
        return

    await state.set_state(RouteStates.waiting_time)

    interests_text = ", ".join(interests_ui)

    await message.answer(
        f"🎯 <b>Отлично! Выбрано:</b> {interests_text}\n\n"
        "⏱️ <b>Шаг 2 из 3: Сколько времени у тебя есть?</b>\n"
        "<i>Выбери из предложенных или введи свое число (например: 2.5)</i>",
        reply_markup=get_time_keyboard()
    )


@router.message(RouteStates.waiting_interests, F.text)
async def process_interests_any_text(message: types.Message, state: FSMContext):
    text = (message.text or "").strip()

    if text == "✅ Готово":
        return

    # Разбираем ввод
    if text in PRESET_INTERESTS:
        ui_items = [text]
    else:
        raw = text.replace("\n", ",")
        ui_items = [x.strip() for x in raw.split(",") if x.strip()]

    if not ui_items:
        await message.answer("❌ Не понял интерес. Введи текстом или выбери кнопку.")
        return

    data = await state.get_data()
    interests = data.get("interests", [])
    interests_ui = data.get("interests_ui", [])

    added_ui = []
    for ui in ui_items:
        # slug для пресетов, иначе — нормализуем “кастом”
        if ui in INTERESTS_MAP:
            slug = INTERESTS_MAP[ui]
        else:
            # кастомный интерес → slug (просто нормализация)
            slug = ui.lower().strip().replace(" ", "_")

        if slug not in interests:
            interests.append(slug)
            interests_ui.append(ui)
            added_ui.append(ui)

    await state.update_data(interests=interests, interests_ui=interests_ui)

    if added_ui:
        await message.answer(f"✅ Добавлено: {', '.join(added_ui)}", reply_markup=get_interests_keyboard())
    else:
        await message.answer("ℹ️ Эти интересы уже добавлены.", reply_markup=get_interests_keyboard())


# ---------- ВРЕМЯ ----------

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


@router.message(RouteStates.waiting_time, F.text)
async def process_time_input(message: types.Message, state: FSMContext):
    """Пользователь ввел время вручную"""
    try:
        time_hours = float((message.text or "").replace(",", ".").strip())

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


# ---------- ЛОКАЦИЯ ----------

@router.message(RouteStates.waiting_location, F.text == "🏙️ Ввести адрес")
async def process_address_request(message: types.Message, state: FSMContext):
    logger.info("process_address_request")
    """Пользователь хочет ввести адрес"""
    await message.answer(
        "🏙️ <b>Введи адрес или название места:</b>\n"
        "<i>Например: Нижегородский кремль, ул. Большая Покровская</i>",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(RouteStates.waiting_location, F.location)
async def process_location(message: types.Message, state: FSMContext):
    logger.info("process_location")
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


@router.message(RouteStates.waiting_location, F.venue)
async def process_venue(message: types.Message, state: FSMContext):
    logger.info("process_venue")
    """Пользователь отправил 'место' (Venue) — тоже считаем как координаты"""
    v = message.venue
    await state.update_data(
        location={
            "type": "venue",
            "text": v.title or "место",
            "lat": v.location.latitude,
            "lon": v.location.longitude,
        }
    )
    await finish_route_creation(message, state)


@router.message(RouteStates.waiting_location, F.text)
async def process_address_input(message: types.Message, state: FSMContext):
    logger.info("process_address_input")
    """Пользователь ввел адрес"""
    address = (message.text or "").strip()

    if not address:
        await message.answer("❌ Введи адрес текстом или отправь геолокацию.")
        return

    # Если человек написал текстом название кнопки — не считаем это адресом
    if address == "📍 Отправить геолокацию":
        await message.answer("Нажми кнопку и разреши доступ к геолокации, либо введи адрес текстом.")
        return

    await state.update_data(
        location={
            "type": "address",
            "text": address,
            "lat": None,
            "lon": None
        }
    )

    await finish_route_creation(message, state)


# ---------- ФИНИШ ----------

async def finish_route_creation(message: types.Message, state: FSMContext):
    logger.info("finish_route_creation")
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

    try:
        response = await api_client.create_route_request(
            telegram_id=message.from_user.id,
            categories=interests,
            time_hours=time_hours,
            location_data=location
        )

        if response.get("success"):
            task_id = response["task_id"]

            await message.answer("⏳ Ожидаю результат от AI Service...")

            result = await gateway_ws.wait_for_task(task_id, timeout=120)

            if result.get("status") in ("ok", "finished"):
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
    """
    Ожидаемый формат:
    {
      "user_id": 4,
      "task_id": "...",
      "output": [{"coordinates":"..","description":".."}, ...],
      "description": "...",
      "time": 1.5,
      "long": 2.5,
      "advice": "...",
      "status": "ok"
    }
    """
    output = result.get("output", [])
    if not output:
        await message.answer(
            "❌ Не удалось построить маршрут (пустой список точек)\n\n"
            "Попробуйте изменить интересы или локацию.",
            reply_markup=get_main_menu_keyboard(is_authenticated=True)
        )
        return

    total_time = result.get("time")     # часы
    total_len = result.get("long")      # км
    desc = result.get("description", "")
    advice = result.get("advice", "")

    # Формируем ссылку на Яндекс маршрут
    yandex_url = _build_yandex_route_url(output, mode="pd")

    # Подробный текст (в стиле “как было у тебя”)
    text = "🗺️ <b>Ваш маршрут готов!</b>\n\n"
    text += f"🎯 <b>Всего точек:</b> {len(output)}\n"
    if total_time is not None:
        text += f"⏱️ <b>Время:</b> {total_time} часов\n"
    if total_len is not None:
        text += f"📏 <b>Длина:</b> {total_len} км\n"

    if desc:
        text += f"\n<b>Описание:</b>\n<i>{desc}</i>\n"

    text += "\n<b>Маршрут включает:</b>\n"
    for i, point in enumerate(output, 1):
        name = point.get("description", f"Точка {i}")
        coords = point.get("coordinates", "")
        text += f"\n{i}. <b>{name}</b>"
        if coords:
            text += f"\n   <code>{coords}</code>"

    if advice:
        text += f"\n\n💡 <b>Совет:</b>\n<i>{advice}</i>"

    # Если ссылка собралась — добавляем кнопку
    if yandex_url:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🗺️ Открыть маршрут в Яндекс Картах", url=yandex_url)]
            ]
        )
        await message.answer(text, reply_markup=kb)
        # отдельным сообщением вернуть меню (чтобы не потерять кнопки бота)
        await message.answer("Что дальше?", reply_markup=get_main_menu_keyboard(is_authenticated=True))
    else:
        # если точек < 2 или координаты не распарсились
        await message.answer(text, reply_markup=get_main_menu_keyboard(is_authenticated=True))


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

@router.message(RouteStates.waiting_location)
async def _debug_waiting_location_catchall(message: types.Message, state: FSMContext):
    """
    Диагностика: если мы реально в waiting_location, сюда попадёт ВСЁ,
    и мы увидим, что приходит (text/location/venue).
    ВАЖНО: этот хендлер временный. Его надо держать последним среди waiting_location.
    """
    st = await state.get_state()
    logger.info(
        "DEBUG waiting_location: state=%s, has_text=%s, has_location=%s, has_venue=%s, content_type=%s, text=%r",
        st,
        bool(message.text),
        bool(message.location),
        bool(message.venue),
        getattr(message, "content_type", None),
        message.text
    )
    await message.answer(
        f"DEBUG: я в состоянии {st}. "
        f"text={bool(message.text)} location={bool(message.location)} venue={bool(message.venue)}"
    )


@router.message(F.text == "❌ Отмена")
async def cancel_route(message: types.Message, state: FSMContext):
    """Отменить создание маршрута"""
    await state.clear()
    await message.answer(
        "❌ Создание маршрута отменено.",
        reply_markup=get_main_menu_keyboard(is_authenticated=True)
    )