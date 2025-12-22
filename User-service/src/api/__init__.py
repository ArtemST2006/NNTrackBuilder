from fastapi import APIRouter
from src.api.handlers import router as users_router

router = APIRouter()

router.include_router(users_router)
