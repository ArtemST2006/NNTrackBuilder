import uuid

from fastapi import APIRouter, HTTPException, status, Depends

from src.kafka.producer import kafka_producer
from src.models.JSONmodels import AcceptResponse, AIRequest
from src.config import KAFKA_TOPIC_AI_REQUEST
from src.midlware.utils import get_current_user_id

router = APIRouter(prefix="/api")

@router.post("/predict", status_code=status.HTTP_202_ACCEPTED, response_model=AcceptResponse)
async def predict(data: AIRequest, user_id: int = Depends(get_current_user_id) ):
    task_id = str(uuid.uuid4())

    message = {
        "depends": "profile",
        "task_id": task_id,
        "user_id": user_id,
        "profile": "",
        "input_data": data.dict()
    }

    try:
        await kafka_producer.send(
            topic=KAFKA_TOPIC_AI_REQUEST,
            value=message,
        )

    except Exception as e:
        print(f"Failed to send to Kafka: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System is busy, please try again later"
        )

    return AcceptResponse(
        task_id=task_id,
        user_id=user_id,
    )