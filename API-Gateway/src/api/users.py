import httpx
from fastapi import APIRouter, HTTPException, status
from src.models.JSONmodels import UserSignInResponse, UserSignIpRequest, UserSignUpRequest
from src.config import USER_SERVICE_URL, logger
from src.midlware.utils import get_password_hash, create_access_token

router = APIRouter(prefix="/api")

@router.post("/sign-up", status_code=status.HTTP_201_CREATED) # create new user
async def sign_up(user_data: UserSignUpRequest):
    async with httpx.AsyncClient() as client:
        try:
            hash_password = get_password_hash(str(user_data.password))
            user_data.password = hash_password
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


@router.post("/sign-in", response_model=UserSignInResponse, status_code=status.HTTP_200_OK) #  log in
async def sign_in(user_data: UserSignIpRequest):
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
    user_id = data.get("user_id")

    access_token = create_access_token(data={"user_id": user_id})

    return UserSignInResponse(
        **data,
        token=access_token,
    )
