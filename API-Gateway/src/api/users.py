import httpx
from fastapi import APIRouter, HTTPException, status
from src.models.JSONmodels import UserSignInResponse, UserSignIpRequest, UserSignUpRequest
from src.config import USER_SERVICE_URL
from src.kafka.producer import kafka_producer
from src.config import *

router = APIRouter()

@router.post("/sign-up", status_code=status.HTTP_200_OK) # create new user
async def sign_up(user_data: UserSignUpRequest):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{USER_SERVICE_URL}/create_user",
                json=user_data.model_dump()
            )

        except httpx.RequestError as e:
            print(f"Connection error: {e}")
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


@router.post("/sign-in", response_model=UserSignInResponse, status_code=status.HTTP_201_CREATED) #  log in
async def sign_in(user_data: UserSignIpRequest):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{USER_SERVICE_URL}/login_user",
                json=user_data.model_dump()
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
