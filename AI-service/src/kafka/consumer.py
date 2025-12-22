import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer
from src.config import (
    KAFKA_BOOTSTRAP,
    KAFKA_GROUP_ID,
    KAFKA_TOPIC_AI_REQUEST,
    KAFKA_TOPIC_AI_RESPONSE,
)
from src.kafka.producer import kafka_producer
from src.services.handler import handle_message
from src.services.rag_wrapper import RAGWrapper

logger = logging.getLogger(__name__)


class KafkaResponseConsumer:
    def __init__(self):
        self.running = False
        self.consumer = None

    async def start(self, rag: RAGWrapper):
        logger.info(f"CONSUMER: Starting... Topic: {KAFKA_TOPIC_AI_REQUEST}, Group: {KAFKA_GROUP_ID}")

        self.consumer = AIOKafkaConsumer(
            KAFKA_TOPIC_AI_REQUEST,
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
                    await self.process_message(data, rag)

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

    async def process_message(self, data: dict, rag: RAGWrapper):
        res = await handle_message(data, rag)

        await kafka_producer.send(KAFKA_TOPIC_AI_RESPONSE, res)


    def stop(self):
        self.running = False


kafka_consumer = KafkaResponseConsumer()