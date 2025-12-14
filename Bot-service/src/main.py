import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import config

# ПРЯМЫЕ ИМПОРТЫ БЕЗ ЧЕРЕЗ __init__.py
from handlers.start import router as start_router
from handlers.help import router as help_router
from handlers.location import router as location_router
from handlers.route import router as route_router

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Основная функция запуска бота"""
    
    try:
        # Проверяем конфигурацию
        config.validate()
        config.print_info()
    except ValueError as e:
        logger.error(f"❌ Ошибка конфигурации: {e}")
        logger.info("💡 Создайте файл Bot-service/.env с BOT_TOKEN=ваш_токен")
        return
    
    # Создаем бота и хранилище состояний
    bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Подключаем роутеры
    dp.include_router(start_router)
    dp.include_router(help_router)
    dp.include_router(location_router)
    dp.include_router(route_router)
    
    # Обработчик неизвестных команд
    # @dp.message()
    # async def handle_unknown(message):
    #     await message.answer(
    #         "🤔 Не понял команду.\n\n"
    #         "Используйте:\n"
    #         "/start - Начало работы\n"
    #         "/route - Создать маршрут\n"
    #         "/help - Помощь"
    #     )
    
    # Получаем информацию о боте
    bot_info = await bot.get_me()
    logger.info(f"✅ Бот запущен: @{bot_info.username} ({bot_info.full_name})")
    logger.info("⏳ Ожидаю сообщения...")
    
    print("🔍 Отладка: Зарегистрированные обработчики")
    for handler in dp.message.handlers:
        print(f"  - Фильтр: {handler.filters}")

    # Запускаем polling
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("👋 Бот остановлен")

if __name__ == "__main__":
    asyncio.run(main())