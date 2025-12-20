import asyncio
import logging
import signal
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from services.websocket_client import gateway_ws

from handlers.start import router as start_router
from handlers.help import router as help_router
from handlers.location import router as location_router
from handlers.auth import router as auth_router
from handlers.route import router as route_router

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


async def shutdown(dispatcher: Dispatcher, bot: Bot):
    logger.info("🛑 Начинаю завершение работы...")
    
    # Закрываем WebSocket соединение
    await gateway_ws.disconnect()
    
    # Закрываем диспетчер
    await dispatcher.storage.close()
    
    # Закрываем сессию бота
    await bot.session.close()
    
    logger.info("✅ Завершение работы выполнено успешно")


async def main():
    logger.info("MAIN CODE VERSION: 2025-12-20-1")
    try:
        # Проверяем конфигурацию
        config.validate()
        config.print_info()
    except ValueError as e:
        logger.error(f"❌ Ошибка конфигурации: {e}")
        logger.info("💡 Создайте файл Bot-service/.env с BOT_TOKEN=ваш_токен")
        return
    
    # Создаем бота
    bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
    
    # Создаем хранилище состояний и диспетчер
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Регистрируем обработчики сигналов для корректного завершения
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        logger.info("📞 Получен сигнал завершения")
        loop.create_task(shutdown(dp, bot))
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)
    
    # Подключаем роутеры
    dp.include_router(start_router)
    logger.info("start_router подключен")
    dp.include_router(help_router)
    logger.info("help_router подключен")
    dp.include_router(auth_router)
    logger.info("auth_router подключен")
    dp.include_router(route_router)
    logger.info("route_router подключен")
    dp.include_router(location_router)
    logger.info("location_router подключен")
    
    # Получаем информацию о боте
    try:
        bot_info = await bot.get_me()
        logger.info(f"🤖 Бот запущен: @{bot_info.username} ({bot_info.full_name})")
        logger.info(f"🌐 API Gateway: {config.API_GATEWAY_URL}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к Telegram API: {e}")
        logger.info("💡 Проверьте BOT_TOKEN в .env файле")
        return
    
    # Проверяем доступность API Gateway
    from services.api_client import api_client
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{config.API_GATEWAY_URL}/docs", timeout=3) as resp:
                if resp.status < 500:
                    logger.info("✅ API Gateway доступен")
                else:
                    logger.warning("⚠️ API Gateway отвечает с ошибкой")
    except:
        logger.warning("⚠️ API Gateway недоступен, некоторые функции могут не работать")
    
    # Очищаем истекшие токены при старте
    from services.token_storage import token_storage
    cleaned = token_storage.cleanup_expired()
    if cleaned > 0:
        logger.info(f"🧹 Очищено {cleaned} истекших токенов")
    
    # Запускаем polling
    logger.info("⏳ Ожидаю сообщения...")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        await shutdown(dp, bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Необработанная ошибка: {e}")