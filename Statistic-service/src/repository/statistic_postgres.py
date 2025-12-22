
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.JSONmodels import AIResponse, StatisticResponse
from src.models.tables import Statistic


class StatisticRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_reports(self, user_id: int) -> StatisticResponse | None:
        query = select(Statistic).where(Statistic.user_id == user_id)
        res = await self.db.execute(query)
        reports = res.scalars().all()

        return StatisticResponse (
            statistic=reports
        )

    async def add_new_predict(self, resp: AIResponse) -> None:
        new_statistic_entry = Statistic(
            user_id=resp.user_id,
            task_id=resp.task_id,
            description=resp.description,
            output=[item.model_dump() for item in resp.output],
            long=resp.long,
            time=resp.time,
            advice=resp.advice,
        )
        self.db.add(new_statistic_entry)
        try:
            await self.db.commit()
            await self.db.refresh(new_statistic_entry)
        except IntegrityError as e:
            await self.db.rollback()
            raise e
        except Exception as e:
            await self.db.rollback()
            raise e