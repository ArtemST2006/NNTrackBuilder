import json
import logging
import asyncio  # <--- Добавил импорт
from aiokafka import AIOKafkaConsumer
from src.config import KAFKA_BOOTSTRAP, KAFKA_TOPIC_RESPONSE, KAFKA_GROUP_ID
from src.managers import manager

logger = logging.getLogger(__name__)


class KafkaResponseConsumer:
    def __init__(self):
        self.running = False
        self.consumer = None

    async def start(self):
        logger.info(f"CONSUMER: Starting... Topic: {KAFKA_TOPIC_RESPONSE}, Group: {KAFKA_GROUP_ID}")
        self.consumer = AIOKafkaConsumer(
            KAFKA_TOPIC_RESPONSE,
            bootstrap_servers=KAFKA_BOOTSTRAP,
            group_id=KAFKA_GROUP_ID,
            auto_offset_reset='latest',
            enable_auto_commit=False,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )

        try:
            await self.consumer.start()
            self.running = True
            logger.info("CONSUMER: Connected and listening.")

            async for msg in self.consumer:
                if not self.running:
                    break

                logger.info(f"CONSUMER: Received message: {msg.value}")
                await self.process_message(msg.value)
                await self.consumer.commit()

        except asyncio.CancelledError:
            logger.info("CONSUMER: Task cancelled. Shutting down gracefully...")

        except Exception as e:
            logger.error(f"CONSUMER: Crashed with error: {e}")

        finally:
            logger.info("CONSUMER: Stopping...")
            self.running = False
            if self.consumer:
                await self.consumer.stop()
            logger.info("CONSUMER: Stopped.")

    async def process_message(self, data: dict):
        user_id = data.get("user_id")
        task_id = data.get("task_id")

        if user_id:
            logger.info(f"CONSUMER: Found active user {user_id}. Sending to WebSocket...")
            payload = {
                "task_id": task_id,
                "status": "finished",
                "payload": data
            }
            await manager.send_message(user_id, payload)
        else:
            logger.warning(f"CONSUMER: Message received without user_id: {user_id}! Data: {data}")

    def stop(self):
        self.running = False


kafka_consumer = KafkaResponseConsumer()