from fastapi import APIRouter
from src.api.ai import router as ai_router
from src.api.statistic import router as stat_router
from src.api.users import router as users_router

router = APIRouter()

router.include_router(users_router)
router.include_router(ai_router)
router.include_router(stat_router)
