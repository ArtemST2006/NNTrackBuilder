import asyncio
import json

from aiokafka import AIOKafkaConsumer
from sqlalchemy.exc import IntegrityError
from src.config import KAFKA_BOOTSTRAP, KAFKA_GROUP_ID, KAFKA_TOPIC_AI_RESPONSE, logger
from src.database import async_session_maker
from src.models.JSONmodels import AIResponse
from src.repository.statistic_postgres import StatisticRepository


class KafkaResponseConsumer:
    def __init__(self):
        self.running = False
        self.consumer = None

    async def start(self):
        logger.info(f"CONSUMER: Starting... Topic: {KAFKA_TOPIC_AI_RESPONSE}")

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
            logger.info("CONSUMER: Connected.")

            async for msg in self.consumer:
                if not self.running:
                    break
                try:
                    data_dict = json.loads(msg.value.decode('utf-8'))

                    logger.info(f"Received JSON: {data_dict}")
                    await self.message(data_dict)

                except json.JSONDecodeError:
                    logger.error(f"BAD JSON SKIP: Не смог прочитать сообщение: {msg.value}")

                except Exception as e:
                    logger.exception(f"Processing Error: {e}")

                finally:
                    await self.consumer.commit()

        except asyncio.CancelledError:
            logger.info("Task cancelled")
        except Exception as e:
            logger.error(f"Critical crash: {e}")
        finally:
            self.running = False
            if self.consumer:
                await self.consumer.stop()

    async def message(self, data: dict) -> None:
        user_id = data.get("user_id")

        if user_id:
            try:
                response_model = AIResponse(**data)
            except Exception as e:
                logger.error(f"Validation error: {e}")
                return

            async with async_session_maker() as session:
                try:
                    repo = StatisticRepository(session)
                    await repo.add_new_predict(response_model)
                except IntegrityError as e:
                    await session.rollback()
                    logger.info(f"Error in repository: {e}")
                except Exception as e:
                    await session.rollback()
                    logger.info(f"Error with add_new_aipredicct: {e}")

    def stop(self):
        self.running = False


kafka_consumer = KafkaResponseConsumer()