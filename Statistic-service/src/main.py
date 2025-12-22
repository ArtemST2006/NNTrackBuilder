import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import router as main_router
from src.config import logger
from src.kafka.consumer import kafka_consumer


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("create new thread fot consumer")
    consumer_task = asyncio.create_task(kafka_consumer.start())

    yield

    logger("system shutting down...")
    kafka_consumer.stop()

    if not consumer_task.done():
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            logger.info("Consumer task successfully cancelled")
    logger.info("shutdown complete.")

app = FastAPI(lifespan=lifespan)
app.include_router(main_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8002,
        reload=True
    )
    if not kafka_consumer.done():
        kafka_consumer.cancel()