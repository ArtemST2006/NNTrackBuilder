import asyncio
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Optional

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.rag_wrapper import RAGWrapper, rag_wrapper

from src.kafka.producer import kafka_producer
from src.kafka.consumer import kafka_consumer

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ai-service")


async def _shutdown(consumer_task: asyncio.Task, rag: RAGWrapper) -> None:
    logger.info("Shutdown: stopping consumer...")
    kafka_consumer.stop()

    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass

    logger.info("Shutdown: stopping producer...")
    await kafka_producer.stop()

    rag.shutdown()

    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)

    logger.info("Shutdown complete.")


async def run() -> None:
    logger.info("Starting Kafka producer...")
    await kafka_producer.start()
    logger.info("Kafka producer started.")

    logger.info("Starting Kafka consumer...")
    consumer_task = asyncio.create_task(kafka_consumer.start(), name="kafka-consumer")
    logger.info("Kafka consumer started.")

    try:
        await consumer_task
    finally:
        await _shutdown(consumer_task, rag_wrapper)


def main() -> None:
    print('he')
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def _on_signal(sig: int, frame: Optional[object] = None) -> None:
        logger.info("Signal %s received, stopping...", sig)
        kafka_consumer.stop()

    # Корректная обработка SIGINT/SIGTERM
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _on_signal, sig, None)
        except NotImplementedError:
            signal.signal(sig, _on_signal)

    loop.run_until_complete(run())


if __name__ == "__main__":
    main()
