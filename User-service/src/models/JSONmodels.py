
from pydantic import BaseModel, EmailStr


class UserSignInRequest(BaseModel):
    email: str
    password: str

class UserSignUpRequest(BaseModel):
    username: str
    email: EmailStr  
    password: str

class UserSignInResponse(BaseModel):
    user_id: int
    username: str
    message: str
    token: str
    telegram_id: str | None = None

class TelegramLinkRequest(BaseModel):
    email: EmailStr
    password: str
    telegram_id: str
    telegram_username: str | None = None

class TelegramUserResponse(BaseModel):
    user_id: int
    username: str
    email: str | None = None
    telegram_id: str | None = None  
    telegram_username: str | None = None
    first_name: str | None = None
    last_name: str | None = None

class TelegramAuthRequest(BaseModel):
    telegram_id: str