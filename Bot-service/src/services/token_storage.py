import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class TokenStorage:
    """
    Хранилище токенов и пользовательских данных в файле JSON

    Структура данных:
    {
        "telegram_id": {
            "token": "jwt_token_here",
            "user_id": 123,
            "email": "user@example.com",
            "username": "john_doe",
            "created_at": "2024-01-15T12:00:00",
            "expires_at": "2024-01-15T13:00:00"
        }
    }
    """

    def __init__(self, file_path: str = "tokens.json"):
        self.file_path = file_path
        self.data: Dict[str, Dict[str, Any]] = {}
        self._load_data()

    def _load_data(self):
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                logger.info(
                    f"📂 Загружено {len(self.data)} токенов из {self.file_path}"
                )
            else:
                self.data = {}
                logger.info(f"📂 Создано новое хранилище токенов")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки токенов: {e}")
            self.data = {}

    def _save_data(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения токенов: {e}")

    def get_token(self, telegram_id: int) -> Optional[str]:
        user_data = self.data.get(str(telegram_id))
        if not user_data:
            return None

        # Проверяем не истек ли токен
        expires_at = user_data.get("expires_at")
        if expires_at:
            try:
                expires_dt = datetime.fromisoformat(expires_at)
                if datetime.now() > expires_dt:
                    logger.info(f"🗑️ Токен истек для пользователя {telegram_id}")
                    self.remove_token(telegram_id)
                    return None
            except ValueError:
                # Некорректный формат даты, игнорируем
                pass

        return user_data.get("token")

    def get_user_id(self, telegram_id: int) -> Optional[int]:
        user_data = self.data.get(str(telegram_id))
        if user_data:
            return user_data.get("user_id")
        return None

    def get_user_data(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        return self.data.get(str(telegram_id))

    def set_token(
        self,
        telegram_id: int,
        token: str,
        user_id: int,
        email: Optional[str] = None,
        username: Optional[str] = None,
        expires_in: int = 3600,
    ):
        created_at = datetime.now()
        expires_at = created_at + timedelta(seconds=expires_in)

        self.data[str(telegram_id)] = {
            "token": token,
            "user_id": user_id,
            "email": email,
            "username": username,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        self._save_data()
        logger.info(
            f"💾 Токен сохранен для пользователя {telegram_id} (user_id: {user_id})"
        )

    def update_user_info(
        self,
        telegram_id: int,
        email: Optional[str] = None,
        username: Optional[str] = None,
    ):
        user_data = self.data.get(str(telegram_id))
        if user_data:
            if email is not None:
                user_data["email"] = email
            if username is not None:
                user_data["username"] = username

            user_data["updated_at"] = datetime.now().isoformat()
            self._save_data()
            logger.info(f"📝 Обновлена информация пользователя {telegram_id}")

    def remove_token(self, telegram_id: int):
        if str(telegram_id) in self.data:
            del self.data[str(telegram_id)]
            self._save_data()
            logger.info(f"🗑️ Токен удален для пользователя {telegram_id}")

    def cleanup_expired(self) -> int:
        expired_count = 0
        current_time = datetime.now()

        telegram_ids = list(self.data.keys())
        for tg_id in telegram_ids:
            user_data = self.data[tg_id]
            expires_at = user_data.get("expires_at")

            if expires_at:
                try:
                    expires_dt = datetime.fromisoformat(expires_at)
                    if current_time > expires_dt:
                        del self.data[tg_id]
                        expired_count += 1
                except ValueError:
                    # Некорректный формат даты, удаляем на всякий случай
                    del self.data[tg_id]
                    expired_count += 1

        if expired_count:
            self._save_data()
            logger.info(f"🧹 Очищено {expired_count} истекших токенов")

        return expired_count

    def get_all_users(self) -> Dict[str, Dict[str, Any]]:
        return self.data.copy()

    def has_token(self, telegram_id: int) -> bool:
        return self.get_token(telegram_id) is not None

    def clear_all(self):
        self.data.clear()
        self._save_data()
        logger.info("🧹 Все токены очищены")


# Глобальный экземпляр хранилища
token_storage = TokenStorage()
