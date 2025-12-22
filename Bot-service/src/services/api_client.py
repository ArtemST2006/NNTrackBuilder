import logging
from typing import Any

import aiohttp
from config import config

from .token_storage import token_storage

logger = logging.getLogger(__name__)


class ApiClient:
    """
    Клиент для работы с API Gateway
    
    Отправляет запросы на создание маршрутов и управление пользователями
    """
    
    def __init__(self, base_url: str = None):
        """
        Инициализация клиента
        
        Args:
            base_url: Базовый URL API Gateway (по умолчанию из config)
        """
        self.base_url = base_url or config.API_GATEWAY_URL
        self.session: aiohttp.ClientSession | None = None
    
    async def __aenter__(self):
        """Контекстный менеджер для автоматического подключения"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер для автоматического отключения"""
        await self.disconnect()
    
    async def connect(self):
        """Создать HTTP сессию"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)  # 30 секунд таймаут
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "User-Agent": "TelegramBot/1.0",
                    "Accept": "application/json"
                }
            )
            logger.info(f"🌐 HTTP клиент подключен к {self.base_url}")
    
    async def disconnect(self):
        """Закрыть HTTP сессию"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("🌐 HTTP клиент отключен")
    
    async def sign_in(self, email: str, password: str) -> dict[str, Any]:
        """
        Авторизация пользователя
        
        Args:
            email: Email пользователя
            password: Пароль пользователя
        
        Returns:
            dict: Результат авторизации с токеном или ошибкой
        """
        await self.connect()
        
        url = f"{self.base_url}/api/sign-in"
        payload = {"email": email, "password": password}
        
        try:
            logger.info(f"🔐 Авторизация пользователя: {email}")
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Успешная авторизация для {email}")
                    return {
                        "success": True,
                        "token": data.get("token"),
                        "user_id": data.get("user_id"),
                        "username": data.get("username"),
                        "message": "Авторизация успешна"
                    }
                elif response.status == 400:
                    error_detail = (await response.json()).get("detail", "Неверные данные")
                    logger.warning(f"❌ Ошибка авторизации: {error_detail}")
                    return {
                        "success": False,
                        "error": "Неверный email или пароль",
                        "details": error_detail
                    }
                elif response.status == 503:
                    logger.error("❌ Сервис авторизации недоступен")
                    return {
                        "success": False,
                        "error": "Сервис недоступен",
                        "details": "Попробуйте позже"
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка сервера при авторизации: {response.status} - {error_text[:200]}")
                    return {
                        "success": False,
                        "error": f"Ошибка сервера: {response.status}",
                        "details": error_text[:200]
                    }
                    
        except aiohttp.ClientConnectionError:
            logger.error("❌ Ошибка подключения к API Gateway")
            return {
                "success": False,
                "error": "Не удалось подключиться к сервису",
                "details": "Проверьте подключение и попробуйте позже"
            }
        except Exception as e:
            logger.error(f"❌ Неизвестная ошибка при авторизации: {e}")
            return {
                "success": False,
                "error": "Внутренняя ошибка",
                "details": str(e)
            }
    
    async def sign_up(self, email: str, username: str, password: str) -> dict[str, Any]:
        """
        Регистрация нового пользователя
        
        Args:
            email: Email пользователя
            username: Имя пользователя
            password: Пароль пользователя
        
        Returns:
            dict: Результат регистрации
        """
        await self.connect()
        
        url = f"{self.base_url}/api/sign-up"
        payload = {
            "email": email,
            "username": username,
            "password": password
        }
        
        try:
            logger.info(f"📝 Регистрация нового пользователя: {email} ({username})")
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 201:
                    logger.info(f"✅ Успешная регистрация для {email}")
                    return {
                        "success": True,
                        "message": "Пользователь успешно создан"
                    }
                elif response.status == 400:
                    error_detail = (await response.json()).get("detail", "Пользователь уже существует")
                    logger.warning(f"❌ Ошибка регистрации: {error_detail}")
                    return {
                        "success": False,
                        "error": "Ошибка регистрации",
                        "details": error_detail
                    }
                elif response.status == 409:
                    error_detail = (await response.json()).get("detail", "Конфликт данных")
                    logger.warning(f"❌ Конфликт при регистрации: {error_detail}")
                    return {
                        "success": False,
                        "error": "Конфликт данных",
                        "details": error_detail
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка сервера при регистрации: {response.status} - {error_text[:200]}")
                    return {
                        "success": False,
                        "error": f"Ошибка сервера: {response.status}",
                        "details": error_text[:200]
                    }
                    
        except aiohttp.ClientConnectionError:
            logger.error("❌ Ошибка подключения к API Gateway")
            return {
                "success": False,
                "error": "Не удалось подключиться к сервису",
                "details": "Проверьте подключение и попробуйте позже"
            }
        except Exception as e:
            logger.error(f"❌ Неизвестная ошибка при регистрации: {e}")
            return {
                "success": False,
                "error": "Внутренняя ошибка",
                "details": str(e)
            }
    
    async def create_route_request(
        self, 
        telegram_id: int,
        categories: list,
        time_hours: float,
        location_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Отправить запрос на создание маршрута
        
        Args:
            telegram_id: Telegram ID пользователя
            categories: Список категорий интересов
            time_hours: Время в часах
            location_data: Данные о локации
        
        Returns:
            dict: Ответ с task_id или ошибкой
        """
        await self.connect()
        
        # Получаем токен и user_id из хранилища
        token = token_storage.get_token(telegram_id)
        user_id = token_storage.get_user_id(telegram_id)
        
        if not token:
            logger.warning(f"❌ Пользователь {telegram_id} не авторизован")
            return {
                "success": False,
                "error": "Требуется авторизация",
                "details": "Пожалуйста, войдите в аккаунт через команду /login"
            }
        
        # Форматируем координаты
        cords = ""
        if location_data.get("lat") and location_data.get("lon"):
            cords = f"{location_data['lat']},{location_data['lon']}"
        
        # Формируем запрос согласно AIRequest модели
        payload = {
            "category": categories,
            "time": time_hours,
            "cords": cords,
            "place": location_data.get("text", "")
        }
        
        url = f"{self.base_url}/api/predict"
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            logger.info(f"🚀 Отправка запроса на создание маршрута для user_id: {user_id}")
            logger.debug(f"📦 Данные запроса: {payload}")
            
            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status == 202:
                    data = await response.json()
                    task_id = data.get("task_id")
                    returned_user_id = data.get("user_id")
                    
                    logger.info(f"✅ Запрос принят, task_id: {task_id}, user_id: {returned_user_id}")
                    return {
                        "success": True,
                        "task_id": task_id,
                        "user_id": returned_user_id,
                        "message": "Запрос на создание маршрута принят"
                    }
                elif response.status == 401:
                    logger.warning(f"❌ Невалидный токен для пользователя {telegram_id}")
                    # Удаляем невалидный токен
                    token_storage.remove_token(telegram_id)
                    return {
                        "success": False,
                        "error": "Сессия истекла",
                        "details": "Пожалуйста, войдите заново"
                    }
                elif response.status == 422:
                    error_detail = (await response.json()).get("detail", "Неверные данные")
                    logger.warning(f"❌ Ошибка валидации: {error_detail}")
                    return {
                        "success": False,
                        "error": "Неверные данные запроса",
                        "details": error_detail
                    }
                elif response.status == 503:
                    logger.error("❌ Сервис маршрутов недоступен")
                    return {
                        "success": False,
                        "error": "Сервис недоступен",
                        "details": "Попробуйте позже"
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка сервера при создании маршрута: {response.status} - {error_text[:200]}")
                    return {
                        "success": False,
                        "error": f"Ошибка сервера: {response.status}",
                        "details": error_text[:200]
                    }
                    
        except aiohttp.ClientConnectionError:
            logger.error("❌ Ошибка подключения к API Gateway")
            return {
                "success": False,
                "error": "Не удалось подключиться к сервису",
                "details": "Проверьте подключение и попробуйте позже"
            }
        except Exception as e:
            logger.error(f"❌ Неизвестная ошибка при создании маршрута: {e}")
            return {
                "success": False,
                "error": "Внутренняя ошибка",
                "details": str(e)
            }
    
    async def get_user_by_telegram(self, telegram_id: str) -> dict[str, Any]:
        """
        Получить пользователя по Telegram ID
        
        Args:
            telegram_id: Telegram ID пользователя
        
        Returns:
            dict: Данные пользователя или ошибка
        """
        await self.connect()
        
        url = f"{self.base_url}/api/user/by-telegram/{telegram_id}"
        
        try:
            logger.info(f"👤 Получение пользователя по Telegram ID: {telegram_id}")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Пользователь найден: {data.get('username')}")
                    return {
                        "success": True,
                        "data": data
                    }
                elif response.status == 404:
                    logger.info(f"ℹ️ Пользователь с Telegram ID {telegram_id} не найден")
                    return {
                        "success": False,
                        "error": "Пользователь не найден",
                        "details": "Пользователь с таким Telegram ID не зарегистрирован"
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка при получении пользователя: {response.status} - {error_text[:200]}")
                    return {
                        "success": False,
                        "error": f"Ошибка сервера: {response.status}",
                        "details": error_text[:200]
                    }
                    
        except aiohttp.ClientConnectionError:
            logger.error("❌ Ошибка подключения к API Gateway")
            return {
                "success": False,
                "error": "Не удалось подключиться к сервису"
            }
        except Exception as e:
            logger.error(f"❌ Неизвестная ошибка: {e}")
            return {
                "success": False,
                "error": "Внутренняя ошибка",
                "details": str(e)
            }

    async def auth_by_telegram(self, telegram_id: str) -> dict[str, Any]:
        """
        Авторизация по Telegram ID
        
        Args:
            telegram_id: Telegram ID пользователя
        
        Returns:
            dict: Результат авторизации с токеном или ошибкой
        """
        await self.connect()
        
        url = f"{self.base_url}/api/auth/telegram"
        payload = {"telegram_id": telegram_id}
        
        try:
            logger.info(f"🔐 Авторизация по Telegram ID: {telegram_id}")
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Успешная авторизация по Telegram ID: {telegram_id}")
                    return {
                        "success": True,
                        "token": data.get("token"),
                        "user_id": data.get("user_id"),
                        "username": data.get("username"),
                        "email": data.get("email"),
                        "telegram_id": data.get("telegram_id"),
                        "message": data.get("message", "Авторизация успешна")
                    }
                elif response.status == 404:
                    logger.info(f"❌ Пользователь с Telegram ID {telegram_id} не найден")
                    return {
                        "success": False,
                        "error": "Пользователь не найден",
                        "details": "Пользователь с таким Telegram ID не зарегистрирован"
                    }
                elif response.status == 400:
                    error_detail = (await response.json()).get("detail", "Ошибка авторизации")
                    logger.warning(f"❌ Ошибка авторизации по Telegram: {error_detail}")
                    return {
                        "success": False,
                        "error": "Ошибка авторизации",
                        "details": error_detail
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка сервера при авторизации по Telegram: {response.status}")
                    return {
                        "success": False,
                        "error": f"Ошибка сервера: {response.status}",
                        "details": error_text[:200]
                    }
                    
        except aiohttp.ClientConnectionError:
            logger.error("❌ Ошибка подключения к API Gateway")
            return {
                "success": False,
                "error": "Не удалось подключиться к сервису",
                "details": "Проверьте подключение и попробуйте позже"
            }
        except Exception as e:
            logger.error(f"❌ Неизвестная ошибка при авторизации по Telegram: {e}")
            return {
                "success": False,
                "error": "Внутренняя ошибка",
                "details": str(e)
            }


# Глобальный экземпляр клиента
api_client = ApiClient()