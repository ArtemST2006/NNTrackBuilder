from passlib.context import CryptContext
import hashlib

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(raw: str, hash: str) -> bool:
    safe_password = hashlib.sha256(raw.encode('utf-8')).hexdigest()
    return pwd_context.verify(safe_password, hash)