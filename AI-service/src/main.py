import asyncio
import logging
import os
import signal
import sys

from src.services.service import Service

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ai-service")

async def main_entry() -> None:
    """Точка входа в асинхронный контекст."""
    service = Service()
    loop = asyncio.get_running_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, service.stop)

    await service.start()

def main() -> None:
    """Запуск Event Loop."""
    try:
        asyncio.run(main_entry())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.critical(f"Fatal error in main loop: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
