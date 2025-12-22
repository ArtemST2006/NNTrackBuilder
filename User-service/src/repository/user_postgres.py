from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.midlware.utils import get_password_hash
from src.models.tables import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, email: str, password: str, username: str) -> User:
        new_user = User(
            email=email,
            password=get_password_hash(password),
            username=username,
        )
        self.db.add(new_user)
        try:
            await self.db.commit()
            await self.db.refresh(new_user)
            return new_user
        except IntegrityError as e:
            await self.db.rollback()
            raise e
        except Exception as e:
            await self.db.rollback()
            raise e

    # МЕТОДЫ ДЛЯ TELEGRAM
    async def get_by_telegram_id(self, telegram_id: str) -> Optional[User]:
        query = select(User).where(User.telegram_id == telegram_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_telegram_info(
        self,
        user_id: int,
        telegram_id: str,
        telegram_username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> User:
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with id {user_id} not found")

        user.telegram_id = telegram_id
        if telegram_username:
            user.telegram_username = telegram_username
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name

        try:
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except IntegrityError as e:
            await self.db.rollback()
            raise e

    async def get_by_id(self, user_id: int) -> Optional[User]:
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_telegram_user(
        self,
        telegram_id: str,
        username: str,
        telegram_username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> User:
        new_user = User(
            telegram_id=telegram_id,
            username=username,
            telegram_username=telegram_username,
            first_name=first_name,
            last_name=last_name,
        )
        self.db.add(new_user)
        try:
            await self.db.commit()
            await self.db.refresh(new_user)
            return new_user
        except IntegrityError as e:
            await self.db.rollback()
            raise e
        except Exception as e:
            await self.db.rollback()
            raise e
