import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from src.api import router as main_router
from src.config import logger
from src.kafka.consumer import kafka_consumer
from src.kafka.producer import kafka_producer
from src.managers import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(">>> System starting...")
    await kafka_producer.start()
    consumer_task = asyncio.create_task(kafka_consumer.start())
    logger.info(">>> Kafka started carefully")

    yield

    logger.info(">>> System shutting down...")
    kafka_consumer.stop()

    if not consumer_task.done():
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            logger.info("Consumer task successfully cancelled")

    await kafka_producer.stop()
    logger.info(">>> Shutdown complete.")


app = FastAPI(lifespan=lifespan)
app.include_router(main_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(user_id, websocket)
    try:
        logger.info("attempt to connect ws")
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(user_id)
        logger.info(f"User {user_id} disconnected")


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
    if not kafka_consumer.done():
        kafka_consumer.cancel()
