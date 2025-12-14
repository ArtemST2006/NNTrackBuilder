from pydantic import BaseModel, EmailStr
from typing import Optional

class UserSignIpRequest(BaseModel):
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
    telegram_id: Optional[str] = None

class TelegramLinkRequest(BaseModel):
    email: EmailStr
    password: str
    telegram_id: str
    telegram_username: Optional[str] = None

class TelegramUserResponse(BaseModel):
    user_id: int
    username: str
    email: Optional[str] = None
    telegram_id: Optional[str] = None  
    telegram_username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None