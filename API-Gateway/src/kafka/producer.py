import json
import logging
from aiokafka import AIOKafkaProducer
from ..config import KAFKA_BOOTSTRAP

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class KafkaProducer:
    def __init__(self):
        self.producer = None

    async def start(self):
        try:
            logger.info(f"PRODUCER: Connecting to {KAFKA_BOOTSTRAP}...")
            self.producer = AIOKafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
            await self.producer.start()
            logger.info("PRODUCER: Connected successfully.")
        except Exception as e:
            logger.error(f"PRODUCER: Failed to start: {e}")
            raise e

    async def stop(self):
        if self.producer:
            await self.producer.stop()
            logger.info("PRODUCER: Stopped.")

    async def send(self, topic: str, value: dict, key: str = None):
        if not self.producer:
            logger.error("PRODUCER: Attempt to send message while producer is not started!")
            raise RuntimeError("Producer is not started")

        try:
            logger.info(f"PRODUCER: Sending message to '{topic}' | Key: {key} | Value: {value}")
            await self.producer.send_and_wait(topic, value=value, key=key)

            logger.info("PRODUCER: Message sent successfully.")
        except Exception as e:
            logger.error(f"PRODUCER: Failed to send message: {e}")
            raise e


kafka_producer = KafkaProducer()