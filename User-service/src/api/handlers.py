from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.models.JSONmodels import UserSignInResponse, UserSignIpRequest, UserSignUpRequest
from src.database import get_db
from src.repository.user_postgres import UserRepository
from src.midlware.utils import verify_password
from src.config import logger

router = APIRouter()

async def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


@router.post("/create_user", status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserSignUpRequest, user_repo: UserRepository = Depends(get_user_repo)):
    existing_user = await user_repo.get_by_email(user_data.email)

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email {user_data.email} already exists"
        )

    try:
        await user_repo.create(
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
        )

        return {"message": "User created successfully"}

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )
    except Exception as e:
        logger.error(f"Internal Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/login_user", status_code=status.HTTP_200_OK, response_model=UserSignInResponse)
async def login(user_data: UserSignIpRequest, user_repo: UserRepository = Depends(get_user_repo)):
    existing_user = await user_repo.get_by_email(user_data.email)

    if not existing_user:
        logger.info("user does not exist")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email {user_data.email} not exist"
        )

    if verify_password(user_data.password, existing_user.password):
        logger.info("password is incorrect")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{user_data.password} - is incorrect password"
        )

    response = UserSignInResponse(
        user_id=existing_user.id,
        username=existing_user.username,
        message="user exists"
    )

    return response
