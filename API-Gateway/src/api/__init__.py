from fastapi import APIRouter

from src.api.users import router as users_router

router = APIRouter()

router.include_router(users_router)