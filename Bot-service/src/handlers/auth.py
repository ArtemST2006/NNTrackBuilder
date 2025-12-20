import logging
from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

from states import AuthStates
from services.api_client import api_client
from services.token_storage import token_storage
from services.websocket_client import gateway_ws
from utils.keyboards import (
    get_main_menu_keyboard, 
    get_auth_keyboard,
    get_cancel_keyboard,
    get_login_choice_keyboard
)
from config import config

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("login"))
@router.message(F.text == "🔐 Войти")
async def cmd_login_choice(message: types.Message, state: FSMContext):
    """
    Показать выбор способа входа
    """
    await state.clear()
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📧 Войти через email",
                    callback_data="login_email"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔗 Войти через WebApp",
                    callback_data="login_webapp"
                )
            ]
        ]
    )
    
    await message.answer(
        "🔐 <b>Выберите способ входа:</b>\n\n"
        "• <b>Через email</b> — стандартный вход по логину и паролю\n"
        "• <b>Через WebApp</b> — удобный интерфейс в браузере\n\n"
        "<i>При первом входе ваш Telegram ID будет привязан к аккаунту</i>",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "login_email")
async def callback_login_email(callback: types.CallbackQuery, state: FSMContext):
    """Начать процесс входа через email"""
    await callback.message.delete()
    await state.set_state(AuthStates.waiting_email)
    
    await callback.message.answer(
        "📧 <b>Вход через email</b>\n\n"
        "Введите ваш email для входа:\n\n"
        "<i>Или используйте /register для регистрации нового аккаунта</i>",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "login_webapp")
async def callback_login_webapp(callback: types.CallbackQuery):
    """Открыть WebApp для входа"""
    try:
        # Получаем URL WebApp из конфигурации
        webapp_url = config.WEBAPP_URL
        
        if not webapp_url:
            await callback.answer(
                "❌ WebApp URL не настроен",
                show_alert=True
            )
            return
        
        # Создаем кнопку с WebApp
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔗 Открыть WebApp для входа",
                        web_app=WebAppInfo(url=webapp_url)
                    )
                ]
            ]
        )
        
        await callback.message.answer(
            "🔐 <b>Вход через WebApp</b>\n\n"
            "Нажмите кнопку ниже чтобы открыть интерфейс входа в браузере.\n"
            "Это удобный способ авторизации с красивым интерфейсом.",
            reply_markup=keyboard
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при открытии WebApp: {e}")
        await callback.answer(
            "⚠️ Ошибка при открытии WebApp. Попробуйте войти через email.",
            show_alert=True
        )

@router.message(Command("register"))
async def cmd_register(message: types.Message, state: FSMContext):
    """Начать процесс регистрации нового пользователя"""
    await state.clear()
    await state.set_state("register_waiting_email")
    
    logger.info(f"📝 Начало регистрации для user_id={message.from_user.id}")
    
    await message.answer(
        "📝 <b>Регистрация нового аккаунта</b>\n\n"
        "Введите email для регистрации:",
        reply_markup=get_cancel_keyboard()
    )


@router.message(StateFilter("register_waiting_email"))
async def process_register_email(message: types.Message, state: FSMContext):
    """Обработать email для регистрации"""
    logger.info(f"📧 Получен email для регистрации: {message.text}")
    
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


@router.message(StateFilter("register_waiting_username"))
async def process_register_username(message: types.Message, state: FSMContext):
    """Обработать имя пользователя для регистрации"""
    logger.info(f"👤 Получено имя пользователя: {message.text}")
    
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


@router.message(StateFilter("register_waiting_password"))
async def process_register_password(message: types.Message, state: FSMContext):
    """Обработать пароль для регистрации"""
    logger.info(f"🔐 Получен пароль для регистрации (длина: {len(message.text)})")
    
    password = message.text
    
    if len(password) < 6:
        await message.answer("❌ Пароль должен быть не менее 6 символов. Попробуйте снова:")
        return
    
    data = await state.get_data()
    email = data.get("email")
    username = data.get("username")
    
    logger.info(f"📦 Регистрация данных: email={email}, username={username}")
    
    await message.answer("⏳ Регистрирую аккаунт...", reply_markup=ReplyKeyboardRemove())
    
    try:
        # Отправляем запрос на регистрацию
        response = await api_client.sign_up(email, username, password)
        
        logger.info(f"📡 Ответ регистрации: {response}")
        
        if response.get("success"):
            await message.answer(
                f"✅ <b>Аккаунт успешно создан!</b>\n\n"
                f"👤 <b>Имя:</b> {username}\n"
                f"📧 <b>Email:</b> {email}\n\n"
                f"Теперь войдите в аккаунт командой /login",
                reply_markup=get_auth_keyboard()
            )
        else:
            error_msg = response.get("error", "Неизвестная ошибка")
            details = response.get("details", "")
            logger.error(f"❌ Ошибка регистрации: {error_msg} - {details}")
            await message.answer(
                f"❌ <b>Ошибка регистрации:</b> {error_msg}\n{details}\n\n"
                "Попробуйте снова командой /register",
                reply_markup=get_auth_keyboard()
            )
    
    except Exception as e:
        logger.error(f"❌ Ошибка регистрации: {e}")
        await message.answer(
            "❌ <b>Ошибка подключения</b>\n\n"
            "Не удалось подключиться к сервису регистрации.",
            reply_markup=get_auth_keyboard()
        )
    
    finally:
        await state.clear()


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
                        user_id=user_id,
                        email=email,
                        username=username
                    )
                    
                    # Привязываем Telegram ID к аккаунту
                    await link_telegram_account(
                        token=token,
                        user=message.from_user,
                        email=email,
                        password=password,
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
                        f"\n\n💡 <b>Telegram ID привязан!</b>\n"
                        f"В следующий раз вход будет автоматическим."
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


async def link_telegram_account(token: str, user: types.User, email: str, password: str) -> bool:
    """Привязать Telegram аккаунт к пользователю"""
    try:
        async with api_client as client:
            headers = {"Authorization": f"Bearer {token}"}
            payload = {
                "email": email,
                "password": password,
                "telegram_id": str(user.id),
                "telegram_username": user.username or "",
            }

            response = await client.session.post(
                f"{client.base_url}/api/link_telegram",
                json=payload,
                headers=headers
            )

            body = await response.text()
            if response.status == 200:
                logger.info("✅ Telegram ID %s успешно привязан", user.id)
                return True

            logger.warning("⚠️ Не удалось привязать Telegram ID: %s body=%s", response.status, body[:800])
            return False

    except Exception as e:
        logger.error("❌ Ошибка привязки Telegram ID: %s", e)
        return False


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
    
    # Получаем email из хранилища
    user_data = token_storage.get_user_data(telegram_id)
    email = user_data.get('email', 'не указан') if user_data else 'не указан'
    username = user_data.get('username', 'не указан') if user_data else 'не указан'
    
    await message.answer(
        f"👤 <b>Ваш профиль</b>\n\n"
        f"👤 <b>Имя:</b> {username}\n"
        f"📧 <b>Email:</b> {email}\n"
        f"🆔 <b>User ID:</b> {user_id}\n"
        f"🤖 <b>Telegram ID:</b> {telegram_id}\n"
        f"🔐 <b>Статус авторизации:</b> Активен ✅\n"
        f"🌐 <b>WebSocket:</b> {ws_status}\n\n"
        f"<i>Используйте /route для создания маршрутов</i>",
        reply_markup=get_main_menu_keyboard(is_authenticated=True)
    )

@router.message(lambda message: message.web_app_data is not None)
async def handle_webapp_data(message: types.Message, state: FSMContext):
    """
    Обработка данных из Telegram WebApp
    
    WebApp отправляет данные в формате:
    {
        "type": "telegram_auth",
        "token": "jwt_token_here",
        "user_id": 123,
        "email": "user@example.com",
        "telegram_id": "123456789"
    }
    """
    try:
        # Парсим данные из WebApp
        webapp_data = json.loads(message.web_app_data.data)
        logger.info(f"📱 Получены данные из WebApp: {webapp_data}")
        
        data_type = webapp_data.get("type")
        
        if data_type != "telegram_auth":
            await message.answer("❌ Неверный тип данных из WebApp")
            return
        
        # Извлекаем данные
        token = webapp_data.get("token")
        user_id = webapp_data.get("user_id")
        email = webapp_data.get("email")
        telegram_id = webapp_data.get("telegram_id")
        username = webapp_data.get("username", "Пользователь")
        
        if not token or not user_id:
            await message.answer("❌ Неполные данные из WebApp")
            return
        
        # Проверяем что Telegram ID совпадает
        if str(telegram_id) != str(message.from_user.id):
            logger.warning(f"⚠️ Несоответствие Telegram ID: WebApp={telegram_id}, Message={message.from_user.id}")
            # Но продолжаем, т.к. могла быть привязка другого аккаунта
        
        # Сохраняем токен
        token_storage.set_token(
            telegram_id=message.from_user.id,
            token=token,
            user_id=user_id,
            email=email,
            username=username
        )
        
        # Подключаем WebSocket
        ws_connected = await gateway_ws.connect(user_id)
        
        # Отправляем приветствие
        success_text = (
            f"✅ <b>Авторизация через WebApp успешна!</b>\n\n"
            f"👤 <b>Аккаунт:</b> {username}\n"
            f"📧 <b>Email:</b> {email}\n"
            f"🆔 <b>ID:</b> {user_id}\n"
        )
        
        if ws_connected:
            success_text += f"\n🌐 <b>WebSocket:</b> Подключен ✅"
        else:
            success_text += f"\n⚠️ <b>WebSocket:</b> Не подключен"
        
        await message.answer(
            success_text,
            reply_markup=get_main_menu_keyboard(is_authenticated=True)
        )
        
        logger.info(f"✅ WebApp авторизация успешна для user_id={user_id}")
        
    except json.JSONDecodeError:
        await message.answer("❌ Ошибка обработки данных из WebApp")
        logger.error("Ошибка декодирования JSON из WebApp")
    except Exception as e:
        await message.answer("❌ Ошибка при обработке данных из WebApp")
        logger.error(f"Ошибка обработки WebApp данных: {e}")
