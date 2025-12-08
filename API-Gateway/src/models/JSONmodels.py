from pydantic import BaseModel


class UserSignIpRequest(BaseModel):
    email: str
    password: str

class UserSignUpRequest(BaseModel):
    username: str
    email: str
    password: str

class UserSignInResponse(BaseModel):
    user_id: int
    username: str
    message: str
