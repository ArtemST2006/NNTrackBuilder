from dotenv import load_dotenv
import logging
import os

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO
)

DB_USER = "user_user"
DB_PASS = "123"
DB_HOST = "postgres"
DB_NAME = "user_db"

# JWT Settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

POSTGRES_DB = os.getenv("POSTGRES_DB", "user_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "user_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", 123)
POSTGRES_PORT = os.getenv("POSTGRES_PORT", 5432)
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")