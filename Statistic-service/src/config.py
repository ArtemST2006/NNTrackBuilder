import os
import logging

logging.basicConfig(
    level=logging.INFO
)
logger = logging.getLogger(__name__)

DB_USER = os.getenv("DB_USER", "user_user")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123")
DB_NAME = os.getenv("DB_NAME", "statistic")
DB_PORT = os.getenv("DB_PORT", "5432")

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9094")
KAFKA_TOPIC_AI_RESPONSE = "ai.makePoints.response"
KAFKA_GROUP_ID = "statistic_gateway_group"