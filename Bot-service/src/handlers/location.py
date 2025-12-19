import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from utils.keyboards import get_main_menu_keyboard

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.location)
async def handle_location_anywhere(message: types.Message, state: FSMContext):
    """
    Обработчик геолокации в любом состоянии
    
    Если пользователь отправил геолокацию вне процесса создания маршрута,
    предлагаем начать создание маршрута от этой точки
    """
    location = message.location
    
    # Проверяем текущее состояние
    current_state = await state.get_state()
    
    if current_state is None:
        # Не в процессе создания маршрута - предлагаем начать
        await message.answer(
            f"📍 <b>Получил вашу локацию!</b>\n\n"
            f"• Широта: {location.latitude:.4f}\n"
            f"• Долгота: {location.longitude:.4f}\n\n"
            "Хотите создать маршрут отсюда?\n"
            "Используйте команду /route",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[
                    [types.KeyboardButton(text="🗺️ Создать маршрут отсюда")],
                    [types.KeyboardButton(text="🔙 Главное меню")]
                ],
                resize_keyboard=True
            )
        )
        
        # Сохраняем локацию во временные данные
        await state.update_data(
            last_location={
                "lat": location.latitude,
                "lon": location.longitude,
                "text": "геолокация"
            }
        )
    
    else:
        # Уже в процессе - просто подтверждаем получение
        await message.answer(f"📍 Локация получена: {location.latitude:.4f}, {location.longitude:.4f}")


@router.message(lambda message: message.text == "🗺️ Создать маршрут отсюда")
async def start_route_from_location(message: types.Message, state: FSMContext):
    """Начать создание маршрута из сохраненной локации"""
    data = await state.get_data()
    location = data.get("last_location")
    
    if not location:
        await message.answer(
            "📍 Сначала отправьте геолокацию",
            reply_markup=get_main_menu_keyboard(is_authenticated=False)
        )
        return
    
    await state.clear()
    
    # Запускаем процесс создания маршрута с сохраненной локацией
    from .route import cmd_route
    await cmd_route(message, state)
    
    # Сохраняем локацию для следующего шага
    await state.update_data(location=location)


@router.message(lambda message: message.text == "🔙 Главное меню")
async def back_to_main_menu(message: types.Message, state: FSMContext):
    """Вернуться в главное меню"""
    await state.clear()
    
    # Проверяем авторизацию для правильного меню
    from ..services.token_storage import token_storage
    telegram_id = message.from_user.id
    token = token_storage.get_token(telegram_id)
    is_authenticated = token is not None
    
    await message.answer(
        "🔙 Возвращаюсь в главное меню...",
        reply_markup=get_main_menu_keyboard(is_authenticated)
    )


@router.message(
    lambda m: m.text and any(
        key in m.text.lower()
        for key in ("ул.", "просп.", "площадь", "кремль", "парк", "музей")
    )
)
async def handle_address_like_message(message: types.Message, state: FSMContext):
    """
    Обработчик сообщений похожих на адреса
    
    Если пользователь отправил что-то похожее на адрес вне процесса
    создания маршрута, предлагаем использовать это для маршрута
    """
    current_state = await state.get_state()
    
    if current_state is None:
        # Не в процессе - предлагаем создать маршрут
        await message.answer(
            f"🏙️ <b>Это похоже на адрес:</b> {message.text}\n\n"
            "Хотите создать маршрут от этого места?\n"
            "Используйте команду /route",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[
                    [types.KeyboardButton(text="🗺️ Создать маршрут отсюда")],
                    [types.KeyboardButton(text="🔙 Главное меню")]
                ],
                resize_keyboard=True
            )
        )
        
        # Сохраняем адрес во временные данные
        await state.update_data(
            last_location={
                "type": "address",
                "text": message.text,
                "lat": None,
                "lon": None
            }
        )