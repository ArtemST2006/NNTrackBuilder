import httpx
from fastapi import APIRouter, HTTPException, status, Depends

from src.config import STATISTIC_SERVICE_URL, logger
from src.midlware.utils import get_current_user_id


router = APIRouter(prefix="/api")

@router.get("/statistic")
async def get_statistic(user_id: int = Depends(get_current_user_id) ):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{STATISTIC_SERVICE_URL}/api/statistic",
                params={"user_id": user_id}
            )

        except httpx.RequestError as e:
            logger.error(f"Connection error: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="User Service is unavailable"
            )

        if response.status_code != 200:
            try:
                error_detail = response.json().get("detail", response.text)
            except:
                error_detail = response.text

            raise HTTPException(
                status_code=response.status_code,
                detail=error_detail
            )

        return response.json()