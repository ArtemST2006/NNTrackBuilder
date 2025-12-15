import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

from ..states import AuthStates
from ..services.api_client import api_client
from ..services.token_storage import token_storage
from ..services.websocket_client import gateway_ws
from ..utils.keyboards import (
    get_main_menu_keyboard, 
    get_auth_keyboard,
    get_cancel_keyboard
)

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("login"))
@router.message(F.text == "🔐 Войти")
async def cmd_login(message: types.Message, state: FSMContext):
    """
    Начать процесс авторизации
    
    Пользователь может войти через email/password
    или зарегистрироваться через /register
    """
    await state.clear()
    await state.set_state(AuthStates.waiting_email)
    
    await message.answer(
        "🔐 <b>Вход в аккаунт</b>\n\n"
        "Введите ваш email для входа:\n\n"
        "<i>Или используйте /register для регистрации нового аккаунта</i>",
        reply_markup=get_cancel_keyboard()
    )


@router.message(Command("register"))
async def cmd_register(message: types.Message, state: FSMContext):
    """
    Начать процесс регистрации нового пользователя
    """
    await state.clear()
    await state.set_state("register_waiting_email")
    
    await message.answer(
        "📝 <b>Регистрация нового аккаунта</b>\n\n"
        "Введите email для регистрации:",
        reply_markup=get_cancel_keyboard()
    )


@router.message(F.text == "❌ Отмена")
async def cancel_auth(message: types.Message, state: FSMContext):
    """Отменить процесс авторизации/регистрации"""
    await state.clear()
    await message.answer(
        "❌ Действие отменено.",
        reply_markup=get_auth_keyboard()
    )


@router.message(AuthStates.waiting_email)
async def process_email(message: types.Message, state: FSMContext):
    """Обработать введенный email для входа"""
    email = message.text.strip()
    
    # Простая валидация email
    if "@" not in email or "." not in email:
        await message.answer(
            "❌ <b>Неверный формат email.</b>\n\n"
            "Пожалуйста, введите корректный email:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(email=email)
    await state.set_state(AuthStates.waiting_password)
    
    await message.answer(
        "🔐 <b>Введите пароль:</b>\n\n"
        "<i>Пароль не будет сохранен в боте, только для проверки на сервере</i>",
        reply_markup=get_cancel_keyboard()
    )


@router.message(AuthStates.waiting_password)
async def process_password(message: types.Message, state: FSMContext):
    """Обработать введенный пароль"""
    password = message.text
    data = await state.get_data()
    email = data.get("email")
    
    await message.answer("⏳ Проверяю данные...", reply_markup=ReplyKeyboardRemove())
    
    try:
        # Отправляем запрос на авторизацию в API Gateway
        async with api_client as client:
            response = await client.session.post(
                f"{client.base_url}/api/sign-in",
                json={"email": email, "password": password}
            )
            
            if response.status == 200:
                auth_data = await response.json()
                token = auth_data.get("token")
                user_id = auth_data.get("user_id")
                username = auth_data.get("username", "Пользователь")
                
                if token and user_id:
                    # Сохраняем токен
                    token_storage.set_token(
                        telegram_id=message.from_user.id,
                        token=token,
                        user_id=user_id
                    )
                    
                    # Подключаемся к WebSocket API Gateway
                    ws_connected = await gateway_ws.connect(user_id)
                    
                    success_text = (
                        f"✅ <b>Вы успешно авторизованы!</b>\n\n"
                        f"👤 <b>Аккаунт:</b> {username}\n"
                        f"📧 <b>Email:</b> {email}\n"
                        f"🆔 <b>ID:</b> {user_id}\n"
                    )
                    
                    if ws_connected:
                        success_text += f"\n🌐 <b>WebSocket:</b> Подключен ✅"
                    else:
                        success_text += f"\n⚠️ <b>WebSocket:</b> Не подключен (переподключимся при создании маршрута)"
                    
                    success_text += (
                        f"\n\nТеперь вы можете создавать персонализированные маршруты!"
                    )
                    
                    await message.answer(
                        success_text,
                        reply_markup=get_main_menu_keyboard(is_authenticated=True)
                    )
                    
                else:
                    await message.answer(
                        "❌ <b>Ошибка:</b> Не получен токен или user_id\n\n"
                        "Попробуйте снова командой /login",
                        reply_markup=get_auth_keyboard()
                    )
            
            elif response.status == 400:
                await message.answer(
                    "❌ <b>Неверный email или пароль</b>\n\n"
                    "Проверьте данные и попробуйте снова:\n"
                    "/login — войти\n"
                    "/register — зарегистрироваться",
                    reply_markup=get_auth_keyboard()
                )
            elif response.status == 503:
                await message.answer(
                    "❌ <b>Сервис авторизации временно недоступен</b>\n\n"
                    "Попробуйте позже или используйте демо-режим.",
                    reply_markup=get_auth_keyboard()
                )
            else:
                error_text = await response.text()
                logger.error(f"Ошибка авторизации: {response.status} - {error_text}")
                await message.answer(
                    f"❌ <b>Ошибка сервера:</b> {response.status}\n\n"
                    "Попробуйте позже.",
                    reply_markup=get_auth_keyboard()
                )
    
    except Exception as e:
        logger.error(f"Ошибка авторизации: {e}")
        await message.answer(
            "❌ <b>Ошибка подключения</b>\n\n"
            "Не удалось подключиться к сервису авторизации. "
            "Попробуйте позже.",
            reply_markup=get_auth_keyboard()
        )
    
    finally:
        await state.clear()


@router.message(F.state == "register_waiting_email")
async def process_register_email(message: types.Message, state: FSMContext):
    """Обработать email для регистрации"""
    email = message.text.strip()
    
    if "@" not in email or "." not in email:
        await message.answer("❌ Неверный формат email. Попробуйте снова:")
        return
    
    await state.update_data(email=email)
    await state.set_state("register_waiting_username")
    
    await message.answer(
        "👤 <b>Введите имя пользователя:</b>\n\n"
        "<i>Это имя будет отображаться в вашем профиле</i>",
        reply_markup=get_cancel_keyboard()
    )


@router.message(F.state == "register_waiting_username")
async def process_register_username(message: types.Message, state: FSMContext):
    """Обработать имя пользователя для регистрации"""
    username = message.text.strip()
    
    if len(username) < 3:
        await message.answer("❌ Имя пользователя должно быть не менее 3 символов. Попробуйте снова:")
        return
    
    await state.update_data(username=username)
    await state.set_state("register_waiting_password")
    
    await message.answer(
        "🔐 <b>Введите пароль:</b>\n\n"
        "<i>Пароль должен быть не менее 6 символов</i>",
        reply_markup=get_cancel_keyboard()
    )


@router.message(F.state == "register_waiting_password")
async def process_register_password(message: types.Message, state: FSMContext):
    """Обработать пароль для регистрации"""
    password = message.text
    
    if len(password) < 6:
        await message.answer("❌ Пароль должен быть не менее 6 символов. Попробуйте снова:")
        return
    
    data = await state.get_data()
    email = data.get("email")
    username = data.get("username")
    
    await message.answer("⏳ Регистрирую аккаунт...", reply_markup=ReplyKeyboardRemove())
    
    try:
        # Отправляем запрос на регистрацию
        async with api_client as client:
            response = await client.session.post(
                f"{client.base_url}/api/sign-up",
                json={
                    "email": email,
                    "username": username,
                    "password": password
                }
            )
            
            if response.status == 201:
                await message.answer(
                    f"✅ <b>Аккаунт успешно создан!</b>\n\n"
                    f"👤 <b>Имя:</b> {username}\n"
                    f"📧 <b>Email:</b> {email}\n\n"
                    f"Теперь войдите в аккаунт командой /login",
                    reply_markup=get_auth_keyboard()
                )
            elif response.status == 400:
                error_detail = (await response.json()).get("detail", "Пользователь уже существует")
                await message.answer(
                    f"❌ <b>Ошибка регистрации:</b> {error_detail}\n\n"
                    "Попробуйте другой email или войдите в существующий аккаунт.",
                    reply_markup=get_auth_keyboard()
                )
            else:
                await message.answer(
                    "❌ <b>Ошибка сервера при регистрации</b>\n\n"
                    "Попробуйте позже.",
                    reply_markup=get_auth_keyboard()
                )
    
    except Exception as e:
        logger.error(f"Ошибка регистрации: {e}")
        await message.answer(
            "❌ <b>Ошибка подключения</b>\n\n"
            "Не удалось подключиться к сервису регистрации.",
            reply_markup=get_auth_keyboard()
        )
    
    finally:
        await state.clear()


@router.message(Command("logout"))
@router.message(F.text == "🚪 Выйти")
async def cmd_logout(message: types.Message):
    """Выйти из аккаунта"""
    telegram_id = message.from_user.id
    
    # Получаем user_id перед удалением токена
    user_id = token_storage.get_user_id(telegram_id)
    
    # Удаляем токен
    token_storage.remove_token(telegram_id)
    
    # Отключаем WebSocket если подключены для этого пользователя
    if user_id and gateway_ws.user_id == user_id:
        await gateway_ws.disconnect()
    
    await message.answer(
        "👋 <b>Вы вышли из аккаунта</b>\n\n"
        "Для использования всех функций снова войдите командой /login",
        reply_markup=get_auth_keyboard()
    )


@router.message(Command("profile"))
@router.message(F.text == "👤 Профиль")
async def cmd_profile(message: types.Message):
    """Показать профиль пользователя"""
    telegram_id = message.from_user.id
    token = token_storage.get_token(telegram_id)
    user_id = token_storage.get_user_id(telegram_id)
    
    if not token:
        await message.answer(
            "🔐 <b>Вы не авторизованы</b>\n\n"
            "Используйте команду /login чтобы войти в аккаунт",
            reply_markup=get_auth_keyboard()
        )
        return
    
    # Проверяем подключение WebSocket
    ws_status = "✅ Подключен" if gateway_ws.is_connected() else "❌ Не подключен"
    
    await message.answer(
        f"👤 <b>Ваш профиль</b>\n\n"
        f"🆔 <b>ID пользователя:</b> {user_id}\n"
        f"🤖 <b>Telegram ID:</b> {telegram_id}\n"
        f"🔐 <b>Статус авторизации:</b> Активен ✅\n"
        f"🌐 <b>WebSocket:</b> {ws_status}\n\n"
        f"<i>Используйте /route для создания маршрутов</i>",
        reply_markup=get_main_menu_keyboard(is_authenticated=True)
    )