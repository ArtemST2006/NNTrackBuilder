import json
import logging
import os

from aiokafka import AIOKafkaProducer

KAFKA_TOPIC_AI_RESPONSE = "ai.makePoints.response"
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9094")

logger = logging.getLogger(__name__)

class KafkaProducer:
    def __init__(self):
        self.producer = None

    async def start(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP,
            acks='all',
            enable_idempotence=True,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None
        )
        await self.producer.start()

    async def stop(self):
        if self.producer:
            await self.producer.stop()

    async def send(self, topic: str, value: dict, key: str = None):
        if not self.producer:
            raise RuntimeError("Producer is not started")

        await self.producer.send_and_wait(topic, value=value, key=key)
        logger.info("message has already sent")


kafka_producer = KafkaProducer()

while True:
    