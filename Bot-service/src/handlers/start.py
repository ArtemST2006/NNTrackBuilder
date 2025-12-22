from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from services.api_client import api_client
from services.token_storage import token_storage
from services.websocket_client import gateway_ws
from utils.keyboards import (
    get_auth_keyboard,
    get_main_menu_keyboard,
)

router = Router()

import logging

logger = logging.getLogger(__name__)


async def try_auto_login(telegram_id: int) -> bool:
    logger.info(f"🔄 Пробую автоматический вход для telegram_id={telegram_id}")
    
    # 1. Проверяем локальное хранилище токенов
    if token_storage.has_token(telegram_id):
        token = token_storage.get_token(telegram_id)
        user_id = token_storage.get_user_id(telegram_id)
        
        logger.info("✅ Найден токен в локальном хранилище")
        if user_id:
            await gateway_ws.connect(user_id)
        return True
    
    # 2. Пробуем авторизоваться по Telegram ID через новый эндпоинт
    logger.info(f"🔍 Пробую авторизацию по telegram_id={telegram_id}")
    try:
        auth_response = await api_client.auth_by_telegram(str(telegram_id))
        
        if auth_response.get("success") and auth_response.get("token"):
            token = auth_response["token"]
            user_id = auth_response["user_id"]
            email = auth_response.get("email", "")
            username = auth_response.get("username", "")
            
            # Сохраняем токен
            token_storage.set_token(
                telegram_id=telegram_id,
                token=token,
                user_id=user_id,
                email=email,
                username=username
            )
            
            # Подключаем WebSocket
            if user_id:
                await gateway_ws.connect(user_id)
            
            logger.info(f"✅ Автоматический вход успешен для user_id={user_id}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Ошибка автоматического входа: {e}")
    
    return False


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    logger.info(f"🚀 /start от user={message.from_user.id}")
    
    # Очищаем состояние
    await state.clear()

    user = message.from_user
    telegram_id = user.id
    
    # Пытаемся автоматически авторизовать
    is_authenticated = await try_auto_login(telegram_id)
    
    if is_authenticated:
        # Уже авторизован (был токен в хранилище)
        welcome_text = f"""
👋 <b>С возвращением, {user.first_name}!</b>

✅ Вы уже авторизованы и можете создавать персонализированные маршруты.

🎯 <b>Доступные команды:</b>
• /route — Создать новый маршрут
• /profile — Показать ваш профиль  
• /logout — Выйти из аккаунта
• /help — Помощь по командам

🚀 <b>Быстрый старт:</b>
Нажмите кнопку ниже чтобы начать создание маршрута!
"""
        keyboard = get_main_menu_keyboard(is_authenticated=True)
        
    else:
        # Не авторизован
        welcome_text = f"""
👋 <b>Привет, {user.first_name}!</b>

🤖 Я — <b>Nizhny Route Builder</b>, твой персональный гид по Нижнему Новгороду.

🎯 <b>Что я умею:</b>
• Создавать персонализированные маршруты
• Учитывать твои интересы (кофейни, музеи, парки и др.)
• Оптимизировать время прогулки
• Подбирать места рядом с тобой

🔐 <b>Чтобы начать:</b>
Войдите в аккаунт, чтобы создавать персонализированные маршруты.

💡 <b>При первом входе:</b>
Ваш Telegram ID будет привязан к аккаунту.
В следующий раз вход будет автоматическим!
"""
        # Показываем только кнопку "Войти"
        keyboard = get_auth_keyboard()
    
    # Отправляем приветствие
    await message.answer(welcome_text, reply_markup=keyboard)


@router.message(Command("about"))
async def cmd_about(message: types.Message):
    about_text = """
ℹ️ <b>О проекте Nizhny Route Builder</b>

🎓 <b>Учебный проект</b> по курсу компьютерных наук
👥 <b>Команда:</b> 4 разработчика
🏗️ <b>Архитектура:</b> Микросервисы + Docker + Kafka
🗺️ <b>Данные:</b> 50+ реальных мест Нижнего Новгорода

🛠️ <b>Технологии:</b>
• Python + FastAPI + Aiogram
• PostgreSQL + SQLAlchemy
• Apache Kafka для асинхронной обработки
• Docker для контейнеризации
• WebSocket для реального времени

🔧 <b>Текущий статус:</b>
✅ Бот запущен и работает
✅ User Service обновлен для Telegram
✅ API Gateway с WebSocket
⏳ AI Service в разработке
🔄 Frontend WebApp в разработке

📊 <b>Возможности бота:</b>
• Авторизация через JWT токены
• Создание персонализированных маршрутов
• Учет интересов и времени
• Реальная асинхронная обработка
• Получение результатов через WebSocket

💡 <b>Для разработчиков:</b>
Исходный код открыт для обучения.
Архитектура может быть использована как шаблон для похожих проектов.
"""
    await message.answer(about_text)


@router.message(lambda message: message.text == "ℹ️ О боте")
async def about_button(message: types.Message):
    """Обработчик кнопки "О боте" из меню"""
    await cmd_about(message)


# Обработчики кнопок главного меню
@router.message(lambda message: message.text == "🗺️ Создать маршрут")
async def create_route_button(message: types.Message, state: FSMContext):
    from .route import cmd_route
    await cmd_route(message, state)


@router.message(lambda message: message.text == "👤 Профиль")
async def profile_button(message: types.Message):
    from .auth import cmd_profile
    await cmd_profile(message)


@router.message(lambda message: message.text == "🔐 Войти")
async def login_button(message: types.Message, state: FSMContext):
    from .auth import cmd_login_choice
    await cmd_login_choice(message, state)


@router.message(lambda message: message.text == "🚪 Выйти")
async def logout_button(message: types.Message):
    from .auth import cmd_logout
    await cmd_logout(message)