import asyncio
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Optional

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.rag_wrapper import RAGWrapper
from src.kafka.producer import kafka_producer
from src.kafka.consumer import kafka_consumer

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ai-service")


class Service:
    def __init__(self) -> None:
        self._shutdown_event = asyncio.Event()
        self._tasks: list[asyncio.Task] = []
        self._rag = RAGWrapper()

    async def start(self) -> None:
        logger.info("Starting Kafka producer...")
        await kafka_producer.start()
        logger.info("Kafka producer started.")

        logger.info("Starting Kafka consumer...")
        consumer_task = asyncio.create_task(
            kafka_consumer.start(_rag), name="kafka-consumer"
        )
        self._tasks.append(consumer_task)
        logger.info("Kafka consumer started.")

        await self._shutdown_event.wait()
        await self.shutdown()

    async def shutdown(self) -> None:
        logger.info("Shutdown initiated...")

        kafka_consumer.stop()

        for task in self._tasks:
            task.cancel()

        await asyncio.gather(*self._tasks, return_exceptions=True)

        logger.info("Stopping Kafka producer...")
        await kafka_producer.stop()

        self._rag.shutdown()

        logger.info("Shutdown complete.")

    def stop(self) -> None:
        self._shutdown_event.set()


def main() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    service = Service()

    def _on_signal(sig: int, frame: Optional[object] = None) -> None:
        logger.info("Signal %s received", sig)
        service.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _on_signal, sig, None)
        except NotImplementedError:
            signal.signal(sig, _on_signal)

    try:
        loop.run_until_complete(service.start())
    finally:
        loop.close()


if __name__ == "__main__":
    main()
