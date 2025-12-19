import os

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9094")
KAFKA_TOPIC_AI_REQUEST = "ai.makePoints.request"
KAFKA_TOPIC_AI_RESPONSE = "ai.makePoints.response"
KAFKA_GROUP_ID = "api_gateway_group"

USER_SERVICE_URL = "http://user-service:8001"
STATISTIC_SERVICE_URL = "http://statistic-service:8002"

# GigaChat
GIGACHAT_API_KEY = os.getenv("GIGACHAT_API_KEY", "")
GIGACHAT_MODEL = os.getenv("GIGACHAT_MODEL", "GigaChat")

# RAG
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://localhost:8001")

# Performance
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))  # Для ThreadPool
RAG_TIMEOUT = int(os.getenv("RAG_TIMEOUT", "120"))  # Таймаут RAG в секундах