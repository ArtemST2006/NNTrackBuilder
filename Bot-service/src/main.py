import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s"
)
logger = logging.getLogger(__name__)

async def main():
    # Получаем токен
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не найден в переменных окружения!")
        return
    
    logger.info("🚀 Запускаю Telegram бота...")
    
    # Создаем бота
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # Получаем информацию о боте
    bot_info = await bot.get_me()
    logger.info(f"✅ Бот идентифицирован: @{bot_info.username} ({bot_info.full_name})")
    
    # Обработчик /start
    @dp.message(Command("start"))
    async def cmd_start(message: Message):
        logger.info(f"👤 Пользователь {message.from_user.id} вызвал /start")
        await message.answer(
            "🤖 <b>Тестовый бот запущен!</b>\n\n"
            "✅ Docker контейнер работает\n"
            "✅ Бот успешно запущен\n"
            "✅ Сообщения доставляются\n\n"
            "Напишите что-нибудь для проверки!"
        )
    
    # Обработчик всех сообщений
    @dp.message()
    async def echo(message: Message):
        logger.info(f"📨 Сообщение от {message.from_user.id}: {message.text}")
        await message.answer(f"📡 Эхо: {message.text}")
    
    # Запускаем бота
    logger.info("⏳ Бот готов к работе...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())