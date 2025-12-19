from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.models.JSONmodels import (
    UserSignInResponse, 
    UserSignInRequest, 
    UserSignUpRequest,
    TelegramLinkRequest,      
    TelegramUserResponse,
    TelegramAuthRequest   
)
from src.database import get_db
from src.repository.user_postgres import UserRepository
from src.midlware.utils import verify_password, create_access_token

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
        print(f"Internal Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/login_user", status_code=status.HTTP_200_OK, response_model=UserSignInResponse)
async def login(user_data: UserSignInRequest, user_repo: UserRepository = Depends(get_user_repo)):
    existing_user = await user_repo.get_by_email(user_data.email)

    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email {user_data.email} not exist"
        )

    if not verify_password(user_data.password, existing_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )

    token = create_access_token(
        data={
            "sub": existing_user.email,
            "user_id": existing_user.id,
            "username": existing_user.username
        }
    )

    response = UserSignInResponse(
        user_id=existing_user.id,
        username=existing_user.username,
        message="Login successful",
        token=token, 
        telegram_id=existing_user.telegram_id  
    )

    return response


# ЭНДПОИНТЫ ДЛЯ TELEGRAM
@router.post("/link_telegram", status_code=status.HTTP_200_OK)
async def link_telegram(
    link_data: TelegramLinkRequest,
    user_repo: UserRepository = Depends(get_user_repo)
):
    """
    Привязать Telegram ID к существующему пользователю
    Требует email и пароль для подтверждения
    """
    # 1. Найти пользователя по email
    user = await user_repo.get_by_email(link_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь с таким email не найден"
        )
    
    # 2. Проверить пароль
    if not verify_password(link_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный пароль"
        )
    
    # 3. Проверить, не привязан ли уже этот telegram_id
    existing_user = await user_repo.get_by_telegram_id(link_data.telegram_id)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Этот Telegram аккаунт уже привязан к другому пользователю"
        )
    
    # 4. Привязать Telegram ID
    try:
        updated_user = await user_repo.update_telegram_info(
            user_id=user.id,
            telegram_id=link_data.telegram_id,
            telegram_username=link_data.telegram_username
        )
        
        return {
            "message": "Telegram аккаунт успешно привязан",
            "user_id": updated_user.id,
            "username": updated_user.username,
            "telegram_id": updated_user.telegram_id
            
        }
    
    except IntegrityError as e:
        print(f"Integrity error: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ошибка при привязке аккаунта"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/by_telegram/{telegram_id}", response_model=TelegramUserResponse)
async def get_user_by_telegram(
    telegram_id: str,
    user_repo: UserRepository = Depends(get_user_repo)
):
    """
    Получить пользователя по Telegram ID
    """
    user = await user_repo.get_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь с таким Telegram ID не найден"
        )
    
    return TelegramUserResponse(
        user_id=user.id,
        username=user.username,
        email=user.email,
        telegram_id=user.telegram_id,
        telegram_username=user.telegram_username,
        first_name=user.first_name,
        last_name=user.last_name
    )

@router.post("/auth/telegram", status_code=status.HTTP_200_OK)
async def auth_by_telegram(
    auth_data: TelegramAuthRequest,
    user_repo: UserRepository = Depends(get_user_repo)
):
    """
    Авторизация по Telegram ID (для автоматического входа в боте)
    Возвращает токен если пользователь найден по telegram_id
    """
    # 1. Найти пользователя по telegram_id
    user = await user_repo.get_by_telegram_id(auth_data.telegram_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь с таким Telegram ID не найден"
        )
    
    # 2. Проверить, что у пользователя есть email (он был зарегистрирован)
    if not user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь зарегистрирован только через Telegram. "
                   "Используйте обычный вход для связи аккаунтов."
        )
    
    # 3. Создать токен
    token = create_access_token(
        data={
            "sub": user.email,
            "user_id": user.id,
            "username": user.username,
            "telegram_id": user.telegram_id
        }
    )
    
    return {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "telegram_id": user.telegram_id,
        "token": token,
        "message": "Авторизация по Telegram успешна"
    }
