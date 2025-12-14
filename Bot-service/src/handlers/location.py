from aiogram import Router, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

router = Router()

@router.message(lambda message: message.location is not None)
async def handle_location(message: types.Message):
    """Обработчик геолокации"""
    location = message.location

    start_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🗺️ Создать маршрут отсюда")],
            [KeyboardButton(text="🎯 Выбрать интересы")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        f"📍 <b>Отлично!</b> Получил твою локацию:\n\n"
        f"• Широта: {location.latitude:.4f}\n"
        f"• Долгота: {location.longitude:.4f}\n\n"
        f"<i>Теперь можем создать маршрут!</i>",
        reply_markup=start_keyboard
    )

@router.message(lambda message: message.text == "🗺️ Создать маршрут отсюда")
async def start_route_from_location(message: types.Message):
    """Начать создание маршрута из полученной локации"""
    await message.answer(
        "🚀 <b>Начинаем создание маршрута!</b>\n\n"
        "🎯 Сначала выбери что тебе интересно:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    
    from ..utils.keyboards import get_interests_keyboard
    await message.answer(
        "Выбери категории (можно несколько):",
        reply_markup=get_interests_keyboard()
    )
    