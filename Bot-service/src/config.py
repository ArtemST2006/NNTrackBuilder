import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Конфигурация бота"""
    
    # Telegram
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

    # Уровень логирования
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # API Gateway
    API_GATEWAY_URL: str = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")
    API_GATEWAY_WS_URL: str = os.getenv("API_GATEWAY_WS_URL", "")
    
    # Kafka (пока не используем, но оставляем)
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    
    # WebSocket
    WS_RECONNECT_DELAY: int = int(os.getenv("WS_RECONNECT_DELAY", "5"))
    WS_TIMEOUT: int = int(os.getenv("WS_TIMEOUT", "120"))
    
    # WebApp (заглушка на будущее)
    WEBAPP_URL: str = os.getenv("WEBAPP_URL", "http://frontend/telegram-auth")
    
    @classmethod
    def validate(cls):
        """Проверяем обязательные настройки"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не установлен в .env файле")
        
        if ":" not in cls.BOT_TOKEN:
            raise ValueError(f"Неверный формат токена: {cls.BOT_TOKEN}")
        
        return True
    
    @classmethod
    def print_info(cls):
        """Выводим информацию о конфигурации"""
        token_preview = f"{cls.BOT_TOKEN[:10]}...{cls.BOT_TOKEN[-4:]}" if cls.BOT_TOKEN else "НЕТ"
        
        print("=== Конфигурация бота ===")
        print(f"🤖 Бот: токен {token_preview}")
        print(f"🚀 API Gateway: {cls.API_GATEWAY_URL}")
        print(f"🌐 WebSocket: {cls.API_GATEWAY_WS_URL or 'авто'}")
        print(f"📡 Kafka: {cls.KAFKA_BOOTSTRAP_SERVERS}")
        print(f"🔄 WS reconnect: {cls.WS_RECONNECT_DELAY} сек")
        print(f"⏱️ WS timeout: {cls.WS_TIMEOUT} сек")
        print(f"📱 WebApp URL: {cls.WEBAPP_URL}")
        print("=========================")

config = Config()