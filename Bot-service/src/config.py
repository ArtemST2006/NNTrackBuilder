import os
from typing import Optional
from dotenv import load_dotenv 

load_dotenv()

class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    API_GATEWAY_URL: str = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    
    # Демо-режим (пока AI Service не готов)
    ENABLE_DEMO_MODE: bool = True
    
    @classmethod
    def validate(cls):
        """Проверяем обязательные настройки"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не установлен в .env файле")
        return True
    
    @classmethod
    def print_info(cls):
        """Выводим информацию о конфигурации"""
        print("=== Конфигурация бота ===")
        print(f"🤖 Бот: токен {'установлен' if cls.BOT_TOKEN else 'НЕ УСТАНОВЛЕН'}")
        print(f"🚀 API Gateway: {cls.API_GATEWAY_URL}")
        print(f"📡 Kafka: {cls.KAFKA_BOOTSTRAP_SERVERS}")
        print(f"🎮 Демо-режим: {'ВКЛ' if cls.ENABLE_DEMO_MODE else 'ВЫКЛ'}")
        print("=========================")

config = Config()
