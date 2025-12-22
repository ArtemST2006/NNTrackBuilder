import httpx
from fastapi import APIRouter, HTTPException, status
from src.config import USER_SERVICE_URL, logger
from src.models.JSONmodels import (
    TelegramAuthRequest,
    TelegramLinkRequest,
    TelegramUserResponse,
    UserSignInRequest,
    UserSignInResponse,
    UserSignUpRequest,
)

router = APIRouter(prefix="/api")

@router.post("/sign-up", status_code=status.HTTP_201_CREATED)
async def sign_up(user_data: UserSignUpRequest):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{USER_SERVICE_URL}/create_user",
                json=user_data.model_dump()
            )

        except httpx.RequestError as e:
            logger.error(f"Connection error: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="User Service is unavailable"
            )

    if response.status_code != 201:
        try:
            error_detail = response.json().get("detail", response.text)
        except:
            error_detail = response.text

        raise HTTPException(
            status_code=response.status_code,
            detail=error_detail
        )

    return response.json()


@router.post("/sign-in", response_model=UserSignInResponse, status_code=status.HTTP_200_OK)
async def sign_in(user_data: UserSignInRequest):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{USER_SERVICE_URL}/login_user",
                json=user_data.model_dump()
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

    data = response.json()

    # User-service теперь сам возвращает токен
    return UserSignInResponse(
        token=data["token"],  # Токен уже есть в ответе User-service
        user_id=data["user_id"],
        username=data["username"],
        message=data["message"],
        telegram_id=data.get("telegram_id")  #  Добавляем telegram_id если есть
    )


# ЭНДПОИНТЫ ДЛЯ TELEGRAM

@router.post("/link_telegram", status_code=status.HTTP_200_OK)
async def link_telegram(link_data: TelegramLinkRequest):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{USER_SERVICE_URL}/link_telegram",
                json=link_data.model_dump()
            )

        except httpx.RequestError as e:
            print(f"Connection error: {e}")
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


@router.post("/auth/telegram", status_code=status.HTTP_200_OK)
async def auth_telegram(auth_data: TelegramAuthRequest):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{USER_SERVICE_URL}/auth/telegram",
                json=auth_data.model_dump()
            )

        except httpx.RequestError as e:
            print(f"Connection error: {e}")
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


@router.get("/user/by-telegram/{telegram_id}", response_model=TelegramUserResponse)
async def get_user_by_telegram(telegram_id: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{USER_SERVICE_URL}/by_telegram/{telegram_id}"
            )

        except httpx.RequestError as e:
            print(f"Connection error: {e}")
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