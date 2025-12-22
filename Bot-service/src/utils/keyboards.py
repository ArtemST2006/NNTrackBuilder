from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove
)
from typing import Optional


def get_interests_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для выбора интересов"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="☕ Кофейни"),
                KeyboardButton(text="🎨 Искусство"),
            ],
            [
                KeyboardButton(text="🏛️ Музей"),
                KeyboardButton(text="🌅 С детьми"),
            ],
            [
                KeyboardButton(text="🏛️ Архитектура"),
                KeyboardButton(text="🌳 Парки"),
            ],
            [
                KeyboardButton(text="🛍️ Магазины"),
                KeyboardButton(text="✏️ Ввести свои варианты"),
                KeyboardButton(text="✅ Готово"),
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_time_keyboard() -> ReplyKeyboardMarkup:
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
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Отправить геолокацию", request_location=True)],
            [KeyboardButton(text="🏙️ Ввести адрес")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_auth_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔐 Войти")],
            [KeyboardButton(text="ℹ️ О боте")]
        ],
        resize_keyboard=True
    )


def get_main_menu_keyboard(is_authenticated: bool = False) -> ReplyKeyboardMarkup:
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


def get_login_choice_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📧 Войти через email",
                    callback_data="login_email"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔗 Войти через WebApp (скоро)",
                    callback_data="login_webapp"
                )
            ]
        ]
    )


def get_yes_no_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Да"), KeyboardButton(text="❌ Нет")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_inline_login_keyboard(webapp_url: Optional[str] = None) -> InlineKeyboardMarkup:
    buttons = []

    if webapp_url:
        buttons.append([
            InlineKeyboardButton(
                text="🔗 Войти через WebApp",
                web_app=webapp_url
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="📧 Войти через email",
            callback_data="login_email"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


# Синонимы для удобства
interests_kb = get_interests_keyboard
time_kb = get_time_keyboard
location_kb = get_location_keyboard
auth_kb = get_auth_keyboard
main_menu_kb = get_main_menu_keyboard
login_choice_kb = get_login_choice_keyboard
yes_no_kb = get_yes_no_keyboard
cancel_kb = get_cancel_keyboard
inline_login_kb = get_inline_login_keyboard
remove_kb = remove_keyboard