import asyncio
import logging

from src.kafka.consumer import kafka_consumer
from src.kafka.producer import kafka_producer
from src.services.rag_wrapper import RAGWrapper

logger = logging.getLogger(__name__)


class Service:
    def __init__(self) -> None:
        self._shutdown_event = asyncio.Event()
        self._consumer_task: asyncio.Task | None = None
        logger.info("Initializing RAG Wrapper...")
        self._rag = RAGWrapper()
        logger.info("RAG Wrapper initialized.")

    async def start(self) -> None:
        """Запуск всех компонентов сервиса."""
        logger.info("Starting Kafka producer...")
        await kafka_producer.start()
        logger.info("Kafka producer started.")

        logger.info("Starting Kafka consumer...")
        self._consumer_task = asyncio.create_task(
            kafka_consumer.start(self._rag),
            name="kafka-consumer"
        )

        self._consumer_task.add_done_callback(self._on_consumer_task_done)

        logger.info("Service is running. Waiting for signals...")

        await self._shutdown_event.wait()

        await self._shutdown()

    def _on_consumer_task_done(self, task: asyncio.Task) -> None:
        """Обработчик падения консьюмера."""
        try:
            task.result()
        except asyncio.CancelledError:
            pass  
        except Exception as e:
            logger.error(f"Kafka consumer task failed unexpectedly: {e}", exc_info=True)
            self.stop()

    def stop(self) -> None:
        """Публичный метод для сигнала остановки."""
        if not self._shutdown_event.is_set():
            logger.info("Stop signal received.")
            self._shutdown_event.set()

    async def _shutdown(self) -> None:
        """Корректное завершение работы."""
        logger.info("Shutdown initiated...")

        if self._consumer_task and not self._consumer_task.done():
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass

        logger.info("Stopping Kafka consumer...")
        if hasattr(kafka_consumer, 'stop'):
            await kafka_consumer.stop()

        logger.info("Stopping Kafka producer...")
        await kafka_producer.stop()

        if hasattr(self._rag, 'shutdown'):
            self._rag.shutdown()

        logger.info("Shutdown complete.")