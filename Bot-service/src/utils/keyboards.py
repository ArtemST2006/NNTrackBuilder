from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    ReplyKeyboardRemove
)
from typing import Optional

def get_interests_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура для выбора интересов при создании маршрута
    
    Returns:
        ReplyKeyboardMarkup: Клавиатура с категориями интересов
    """
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
    """
    Клавиатура для выбора времени прогулки
    
    Returns:
        ReplyKeyboardMarkup: Клавиатура с вариантами времени
    """
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
    """
    Клавиатура для получения локации от пользователя
    
    Returns:
        ReplyKeyboardMarkup: Клавиатура с кнопками локации
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Отправить геолокацию", request_location=True)],
            [KeyboardButton(text="🏙️ Ввести адрес")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_auth_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура для неавторизованных пользователей
    
    Returns:
        ReplyKeyboardMarkup: Клавиатура с опциями авторизации
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔐 Войти")],
            [KeyboardButton(text="🗺️ Демо-маршрут")],
            [KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True
    )


def get_main_menu_keyboard(is_authenticated: bool = False) -> ReplyKeyboardMarkup:
    """
    Главное меню в зависимости от статуса авторизации
    
    Args:
        is_authenticated: Авторизован ли пользователь
    
    Returns:
        ReplyKeyboardMarkup: Соответствующая клавиатура
    """
    if is_authenticated:
        # Меню для авторизованных пользователей
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🗺️ Создать маршрут")],
                [KeyboardButton(text="👤 Профиль")],
                [KeyboardButton(text="🚪 Выйти")]
            ],
            resize_keyboard=True
        )
    else:
        # Меню для неавторизованных пользователей
        return get_auth_keyboard()


def get_yes_no_keyboard() -> ReplyKeyboardMarkup:
    """
    Простая клавиатура Да/Нет
    
    Returns:
        ReplyKeyboardMarkup: Клавиатура с кнопками Да и Нет
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Да"), KeyboardButton(text="❌ Нет")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура с кнопкой отмены
    
    Returns:
        ReplyKeyboardMarkup: Клавиатура с кнопкой Отмена
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_inline_login_keyboard(webapp_url: Optional[str] = None) -> InlineKeyboardMarkup:
    """
    Inline клавиатура для входа через WebApp
    
    Args:
        webapp_url: URL WebApp для аутентификации
    
    Returns:
        InlineKeyboardMarkup: Inline клавиатура с кнопками
    """
    buttons = []
    
    if webapp_url:
        # Кнопка для входа через WebApp
        buttons.append([
            InlineKeyboardButton(
                text="🔗 Войти через WebApp",
                web_app=webapp_url
            )
        ])
    
    # Кнопка для обычного входа
    buttons.append([
        InlineKeyboardButton(
            text="📧 Войти через email",
            callback_data="login_email"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def remove_keyboard() -> ReplyKeyboardRemove:
    """
    Убрать клавиатуру
    
    Returns:
        ReplyKeyboardRemove: Объект для удаления клавиатуры
    """
    return ReplyKeyboardRemove()


# Синонимы для удобства
interests_kb = get_interests_keyboard
time_kb = get_time_keyboard
location_kb = get_location_keyboard
auth_kb = get_auth_keyboard
main_menu_kb = get_main_menu_keyboard
yes_no_kb = get_yes_no_keyboard
cancel_kb = get_cancel_keyboard
inline_login_kb = get_inline_login_keyboard
remove_kb = remove_keyboard