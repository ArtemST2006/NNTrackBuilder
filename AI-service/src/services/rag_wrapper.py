import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Dict, Any, Optional

from rag.scripts.search import HybridSearcher

logger = logging.getLogger(__name__)

class RAGWrapper:
    def __init__(self, db_path: Optional[str] = None, max_workers: int = 4):
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="RAG_Worker"
        )

        if db_path is None:
            project_root = Path(__file__).resolve().parents[2]
            db_path = str(project_root / "rag" / "chroma_db")

        logger.info(f"RAG: init HybridSearcher with db_path={db_path}")
        self._searcher = HybridSearcher(db_path=str(db_path))

    async def search_raw(self, query: str, user_lat: Optional[float] = None, user_lon: Optional[float] = None,
                         n_results: int = 5) -> List[Dict[str, Any]]:
        loop = asyncio.get_running_loop()

        def _call():
            return self._searcher.search(query=query, user_lat=user_lat, user_lon=user_lon, n_results=n_results)

        logger.info(f"RAG: search '{query[:80]}'")

        results = await loop.run_in_executor(self._executor, _call)

        logger.info(f"RAG: found {len(results)} results")
        return results

    def shutdown(self):
        self._executor.shutdown(wait=True)
        logger.info("RAG: executor shutdown")

