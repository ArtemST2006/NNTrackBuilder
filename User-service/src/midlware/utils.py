from passlib.context import CryptContext
import hashlib
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional
from .. import config  

# Для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(raw: str, hash: str) -> bool:
    safe_password = hashlib.sha256(raw.encode('utf-8')).hexdigest()
    return pwd_context.verify(safe_password, hash)

def get_password_hash(password: str) -> str:
    """Захешировать пароль"""
    safe_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return pwd_context.hash(safe_password)

# ИСПОЛЬЗУЕМ НАСТРОЙКИ ИЗ CONFIG
SECRET_KEY = config.SECRET_KEY
ALGORITHM = config.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = config.ACCESS_TOKEN_EXPIRE_MINUTES

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        SECRET_KEY, 
        algorithm=ALGORITHM
    )
    
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM]
        )
        return payload
    except JWTError:
        return None