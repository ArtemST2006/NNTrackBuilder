import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn

from src.api.users import router as users_router
from src.config import KAFKA_TOPIC_REQUEST
from src.kafka.producer import kafka_producer
from src.kafka.consumer import kafka_consumer
from src.managers import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(">>> System starting...")
    await kafka_producer.start()
    consumer_task = asyncio.create_task(kafka_consumer.start())

    yield

    print(">>> System shutting down...")
    kafka_consumer.stop()

    if not consumer_task.done():
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            print("Consumer task successfully cancelled")

    await kafka_producer.stop()
    print(">>> Shutdown complete.")


app = FastAPI(lifespan=lifespan)
app.include_router(users_router)

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
    if not kafka_consumer.done():
        kafka_consumer.cancel()
