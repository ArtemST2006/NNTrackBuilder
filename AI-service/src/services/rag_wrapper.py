import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Any, List, Optional

from rag.scripts.search import HybridSearcher

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=4)


class RagWrapper:
    def __init__(self, db_path: Optional[str] = None):
        if (db_path is None) or (db_path == ""):
            project_root = Path(__file__).resolve().parent.parent
            dp_path = project_root / "chrome_db"

        logger.info(f"RAG: init HybridSearcher with db_path='{db_path}'")
        self._searcher = HybridSearcher(db_path=str(db_path))

    async def search_place(self,
                           query: str,
                           categories: Optional[List[str]] = None,
                           time_hours: Optional[float] = None,
                           cords: Optional[str] = None,
                           place: Optional[str] = None,
                           n_results: int = 5, ) -> List[Dict[str, Any]]:
        """
        Асинхронный вызов HybridSearcher.search в отдельном потоке.
        Сейчас используем только query и n_results.
        """

        loop = asyncio.get_event_loop()

        def _call():
            # пока игнорируем categories/time/cords/place,
            # если решите маппить на search_categories/filters — допишем
            return self._searcher.search(query=query,
                                         n_results=n_results)

        logger.info(f"RAG: search '{query[:80]}'")
        results = await loop.run_in_executor(_executor, _call)
        logger.info(f"RAG: found {len(results)} results")

        return results

    def shutdown(self):
        _executor.shutdown(wait=True)
        logger.info("RAG: executor shutdown")

rag_wrapper = RagWrapper()

