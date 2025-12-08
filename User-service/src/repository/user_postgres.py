from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
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
            password=password,
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