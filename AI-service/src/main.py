import asyncio
import json
import logging
import os
import signal
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

from src.config import (
    KAFKA_TOPIC_AI_REQUEST,
    KAFKA_TOPIC_AI_RESPONSE,
)
from src.kafka.consumer import kafka_consumer
from src.kafka.producer import kafka_producer
from src.managers import manager
from src.services.handler import handle_message

logger = logging.getLogger("ai-service")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # logging
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # kafka producer
    logger.info("Starting Kafka producer...")
    await kafka_producer.start()
    logger.info("Kafka producer started.")

    # kafka consumer (response) in background task
    logger.info("Starting Kafka response consumer...")
    consumer_task = asyncio.create_task(kafka_consumer.start())
    logger.info("Kafka response consumer task started.")

    try:
        yield
    finally:
        logger.info("Shutting down...")
        kafka_consumer.stop()

        # cancel task
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass

        await kafka_producer.stop()
        logger.info("Shutdown complete.")


app = FastAPI(title="AI Service", lifespan=lifespan)


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.websocket("/ws/{user_id}")
async def ws_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(user_id, websocket)
    logger.info("WS connected: user_id=%s", user_id)

    try:
        while True:
            # Клиент может прислать задачу напрямую в WS:
            # { "task_id": "...", "input_data": {...}, ... }
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json(
                    {"status": "error", "error": "Invalid JSON", "raw": raw}
                )
                continue

            # 1) обработать локально (RAG + gigachat) и отправить в Kafka response
            # 2) ИЛИ отправить в Kafka request для отдельного воркера
            # Здесь сделаю вариант: обрабатываем и публикуем в RESPONSE.
            try:
                # гарантируем user_id
                data["user_id"] = int(user_id) if str(user_id).isdigit() else user_id
                result = await handle_message(data)

                # публикуем в response topic (чтобы consumer разослал в WS и/или другие сервисы)
                await kafka_producer.send(
                    topic=KAFKA_TOPIC_AI_RESPONSE,
                    value=result,
                    key=str(data.get("task_id") or user_id),
                )

                # и сразу ответим по WS (чтобы не ждать roundtrip Kafka)
                await websocket.send_json({"status": "accepted", "task_id": data.get("task_id")})

            except Exception as e:
                logger.exception("WS handling error user_id=%s: %s", user_id, e)
                await websocket.send_json({"status": "error", "error": str(e)})

    except WebSocketDisconnect:
        logger.info("WS disconnected: user_id=%s", user_id)
        manager.disconnect(user_id)
    except Exception as e:
        logger.exception("WS error user_id=%s: %s", user_id, e)
        manager.disconnect(user_id)


@app.post("/tasks")
async def create_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    HTTP вход для постановки задачи.
    Отправляем в Kafka request topic, чтобы другой воркер/консьюмер обработал.
    """
    task_id = payload.get("task_id")
    if not task_id:
        return {"status": "error", "error": "task_id is required"}

    await kafka_producer.send(
        topic=KAFKA_TOPIC_AI_REQUEST,
        value=payload,
        key=str(task_id),
    )
    return {"status": "queued", "task_id": task_id}


def _install_signal_handlers():
    """
    Uvicorn сам корректно останавливает приложение,
    но если запускаешь main.py напрямую — полезно иметь явные хендлеры.
    """
    loop = asyncio.get_event_loop()

    def _handler(sig: int, frame: Optional[object] = None):
        logger.info("Received signal %s, stopping...", sig)
        # stop consumer loop
        kafka_consumer.stop()

    for s in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(s, _handler)  # type: ignore[arg-type]
        except Exception:
            # на некоторых платформах/в некоторых окружениях может не поддерживаться
            pass


if __name__ == "__main__":
    _install_signal_handlers()
    uvicorn.run(
        "src.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        log_level=LOG_LEVEL.lower(),
    )
