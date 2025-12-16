import json
import logging
import asyncio
from aiokafka import AIOKafkaConsumer
from src.config import KAFKA_BOOTSTRAP, KAFKA_TOPIC_AI_RESPONSE, KAFKA_GROUP_ID
from src.managers import manager

logger = logging.getLogger(__name__)


class KafkaResponseConsumer:
    def __init__(self):
        self.running = False
        self.consumer = None

    async def start(self):
        logger.info(f"CONSUMER: Starting... Topic: {KAFKA_TOPIC_AI_RESPONSE}, Group: {KAFKA_GROUP_ID}")

        self.consumer = AIOKafkaConsumer(
            KAFKA_TOPIC_AI_RESPONSE,
            bootstrap_servers=KAFKA_BOOTSTRAP,
            group_id=KAFKA_GROUP_ID,
            auto_offset_reset='latest',
            enable_auto_commit=False
        )

        try:
            await self.consumer.start()
            self.running = True
            logger.info("CONSUMER: Connected and listening.")

            async for msg in self.consumer:
                if not self.running:
                    break
                try:
                    if msg.value is None:
                        continue
                    data = json.loads(msg.value.decode('utf-8'))

                    logger.info(f"CONSUMER: Received message: {data}")
                    await self.process_message(data)

                except json.JSONDecodeError as e:
                    logger.error(f"CONSUMER: JSON Decode Error (Skipping). Error: {e}. Raw: {msg.value}")

                except Exception as e:
                    logger.exception(f"CONSUMER: Error processing message: {e}")

                finally:
                    await self.consumer.commit()

        except asyncio.CancelledError:
            logger.info("CONSUMER: Task cancelled. Shutting down gracefully...")

        except Exception as e:
            logger.error(f"CONSUMER: Critical crash: {e}")

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
            logger.info(f"CONSUMER: {user_id}. Sending to WebSocket...")
            payload = {
                "task_id": task_id,
                "status": "finished",
                "payload": data
            }
            try:
                await manager.send_message(user_id, payload)
            except Exception as e:
                logger.error(f"CONSUMER: Failed to send to WebSocket user {user_id}: {e}")
        else:
            logger.warning(f"CONSUMER: Message received without user_id: {user_id}! Data: {data}")

    def stop(self):
        self.running = False


kafka_consumer = KafkaResponseConsumer()