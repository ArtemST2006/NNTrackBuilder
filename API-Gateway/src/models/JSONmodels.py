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
    telegram_id: str | None = None  


class TelegramAuthRequest(BaseModel):
    telegram_id: str


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
    output: list[PlaceItem]
    description: str
    time: float
    long: float
    advice: str


class StatisticResponse(BaseModel):
    statistic: list[AIResponse]