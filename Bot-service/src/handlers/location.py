import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from states import RouteStates
from utils.keyboards import get_main_menu_keyboard

router = Router()
logger = logging.getLogger(__name__)


def _is_route_flow_state(state_name: str | None) -> bool:
    if not state_name:
        return False
    # В aiogram state обычно выглядит как "RouteStates:waiting_location"
    return state_name.startswith("RouteStates:")


@router.message(F.location)
async def handle_location_anywhere(message: types.Message, state: FSMContext):
    current_state = await state.get_state()

    # ВАЖНО: не перехватываем гео в процессе /route
    if _is_route_flow_state(current_state):
        return

    location = message.location

    await message.answer(
        f"📍 <b>Получил вашу локацию!</b>\n\n"
        f"• Широта: {location.latitude:.4f}\n"
        f"• Долгота: {location.longitude:.4f}\n\n"
        "Хотите создать маршрут отсюда?\n"
        "Используйте команду /route",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="🗺️ Создать маршрут отсюда")],
                [types.KeyboardButton(text="🔙 Главное меню")],
            ],
            resize_keyboard=True,
        ),
    )

    await state.update_data(
        last_location={
            "type": "coordinates",
            "lat": location.latitude,
            "lon": location.longitude,
            "text": "геолокация",
        }
    )


@router.message(F.text == "🗺️ Создать маршрут отсюда")
async def start_route_from_location(message: types.Message, state: FSMContext):
    data = await state.get_data()
    location = data.get("last_location")

    if not location:
        await message.answer(
            "📍 Сначала отправьте геолокацию",
            reply_markup=get_main_menu_keyboard(is_authenticated=False),
        )
        return

    # импорт внутри, чтобы не было циклических импортов на уровне модуля
    from handlers.route import cmd_route

    # Запускаем сценарий маршрута
    await cmd_route(message, state)

    # СРАЗУ кладём локацию и переводим на processing
    # (так пользователь может начать маршрут “отсюда” без шага 3)
    await state.update_data(location=location)


@router.message(F.text == "🔙 Главное меню")
async def back_to_main_menu(message: types.Message, state: FSMContext):
    await state.clear()

    from services.token_storage import token_storage

    telegram_id = message.from_user.id
    token = token_storage.get_token(telegram_id)
    is_authenticated = token is not None

    await message.answer(
        "🔙 Возвращаюсь в главное меню...",
        reply_markup=get_main_menu_keyboard(is_authenticated),
    )


@router.message(
    F.text
    & (
        F.text.lower().contains("ул.")
        | F.text.lower().contains("просп.")
        | F.text.lower().contains("площад")
        | F.text.lower().contains("кремл")
        | F.text.lower().contains("парк")
        | F.text.lower().contains("музей")
    )
)
async def handle_address_like_message(message: types.Message, state: FSMContext):
    current_state = await state.get_state()

    # ВАЖНО: не перехватываем адреса в процессе /route
    if _is_route_flow_state(current_state):
        return

    await message.answer(
        f"🏙️ <b>Это похоже на адрес:</b> {message.text}\n\n"
        "Хотите создать маршрут от этого места?\n"
        "Используйте команду /route",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="🗺️ Создать маршрут отсюда")],
                [types.KeyboardButton(text="🔙 Главное меню")],
            ],
            resize_keyboard=True,
        ),
    )

    await state.update_data(
        last_location={
            "type": "address",
            "text": message.text,
            "lat": None,
            "lon": None,
        }
    )
