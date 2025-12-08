import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn

from src.api.handlers import router as users_router
# from .kafka.producer import kafka_producer
# from .kafka.consumer import kafka_consumer


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     print(">>> System starting...")
#     await kafka_producer.start()
#     consumer_task = asyncio.create_task(kafka_consumer.start())
#
#     yield
#
#     print(">>> System shutting down...")
#     kafka_consumer.stop()
#
#     if not consumer_task.done():
#         consumer_task.cancel()
#         try:
#             await consumer_task
#         except asyncio.CancelledError:
#             print("Consumer task successfully cancelled")
#
#     await kafka_producer.stop()
#     print(">>> Shutdown complete.")


# app = FastAPI(lifespan=lifespan)
app = FastAPI()
app.include_router(users_router)

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )