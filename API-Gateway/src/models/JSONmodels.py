import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr


class UserSignInRequest(BaseModel):  
    email: str
    password: str


class UserSignUpRequest(BaseModel):
    username: str
    email: str
    password: str


class UserSignInResponse(BaseModel):
    token: str
    user_id: int
    username: str
    message: str
    telegram_id: Optional[str] = None  


class TelegramAuthRequest(BaseModel):
    telegram_id: str


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


class AIRequest(BaseModel):
    category: list
    time: float
    cords: str
    place: str


class AcceptResponse(BaseModel):
    user_id: int
    task_id: str


class PlaceItem(BaseModel):
    coordinates: str
    description: str


class AIResponse(BaseModel):
    user_id: int
    task_id: str
    output: List[PlaceItem]
    description: str
    time: float
    long: float
    advice: str


class StatisticResponse(BaseModel):
    statistic: List[AIResponse]