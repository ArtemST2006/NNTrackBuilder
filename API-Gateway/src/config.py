import os

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9094")
KAFKA_TOPIC_AI_REQUEST = "ai.makePoints.request"
KAFKA_TOPIC_AI_RESPONSE = "ai.makePoints.response"
KAFKA_GROUP_ID = "api_gateway_group"

USER_SERVICE_URL = "http://user-service:8001"