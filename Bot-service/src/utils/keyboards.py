from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_interests_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для выбора интересов"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="☕ Кофейни"),
                KeyboardButton(text="🎨 Стрит-арт"),
            ],
            [
                KeyboardButton(text="🏛️ Музеи"),
                KeyboardButton(text="🌅 Панорамы"),
            ],
            [
                KeyboardButton(text="🏛️ Архитектура"),
                KeyboardButton(text="🌳 Парки"),
            ],
            [
                KeyboardButton(text="🛍️ Магазины"),
                KeyboardButton(text="✅ Готово"),
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_time_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для выбора времени"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1 час"), KeyboardButton(text="2 часа")],
            [KeyboardButton(text="3 часа"), KeyboardButton(text="4 часа")],
            [KeyboardButton(text="Другое время...")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_location_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для получения локации"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Отправить геолокацию", request_location=True)],
            [KeyboardButton(text="🏙️ Ввести адрес")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )