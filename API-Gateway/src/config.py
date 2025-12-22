import logging
import os

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
)

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9094")
KAFKA_TOPIC_AI_REQUEST = os.getenv("KAFKA_TOPIC_AI_REQUEST", "ai.makePoints.request")
KAFKA_TOPIC_AI_RESPONSE = os.getenv("KAFKA_TOPIC_AI_RESPONSE", "ai.makePoints.response")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "api_gateway_group")

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8001")
STATISTIC_SERVICE_URL = os.getenv("STATISTIC_SERVICE_URL", "http://localhost:8002")
