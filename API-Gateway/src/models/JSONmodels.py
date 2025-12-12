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
    time: float
    cords: str
    place: str


class AcceptResponse(BaseModel):
    user_id: int
    task_id: str


