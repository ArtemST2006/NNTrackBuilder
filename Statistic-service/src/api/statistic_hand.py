from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import logger
from src.models.JSONmodels import StatisticResponse
from src.repository.statistic_postgres import StatisticRepository

from src.database import get_db

router = APIRouter(prefix="/api")


def get_stat_db(db: AsyncSession = Depends(get_db)) -> StatisticRepository:
    return StatisticRepository(db)


@router.get(
    "/statistic", response_model=StatisticResponse, status_code=status.HTTP_200_OK
)
async def statistic(user_id: int, repo: StatisticRepository = Depends(get_stat_db)):
    try:
        response = await repo.get_reports(user_id)
        logger.info("success result of get statistic")
        return response
    except Exception:
        logger.error("error with get statistic")
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="server error"
        )
