import os

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9094")
KAFKA_TOPIC_AI_REQUEST = "ai.makePoints.request"
KAFKA_TOPIC_AI_RESPONSE = "ai.makePoints.response"
KAFKA_GROUP_ID = "api_gateway_group"

USER_SERVICE_URL = "http://user-service:8001"
STATISTIC_SERVICE_URL = "http://statistic-service:8002"

MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))


# Ключ авторизации GigaChat (Authorization Key из ЛК, НЕ access_token)
GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS")

# Скоуп API
GIGACHAT_SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")

# Модель (опционально)
GIGACHAT_MODEL = os.getenv("GIGACHAT_MODEL", "GigaChat-2")

# Проверка сертификатов (для dev можно False, для prod лучше True)
GIGACHAT_VERIFY_SSL_CERTS = os.getenv("GIGACHAT_VERIFY_SSL_CERTS", "False").lower() == "true"

