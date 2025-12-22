from fastapi import APIRouter
from src.api.statistic_hand import router as stat_router

router = APIRouter()
router.include_router(stat_router)
