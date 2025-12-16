import datetime
from typing import List

from pydantic import BaseModel


class UserSignIpRequest(BaseModel):
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

class AIRequest(BaseModel):
    category: list
    time: float # вреям которое пользователь готов потратить на прогулку
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
    time: datetime.datetime
    long: float
    advice: str


class StatisticResponse(BaseModel):
    statistic: List[AIResponse]


