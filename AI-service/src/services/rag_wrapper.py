import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Dict, Any, Optional

from rag.scripts.search import HybridSearcher

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=4)


class RAGWrapper:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            project_root = Path(__file__).resolve().parents[2]
            db_path = str(project_root / "chroma_db")

        logger.info(f"RAG: init HybridSearcher with db_path={db_path}")
        self._searcher = HybridSearcher(db_path=str(db_path))

    async def search_raw(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        loop = asyncio.get_event_loop()

        def _call():
            return self._searcher.search(query=query, n_results=n_results)

        logger.info(f"RAG: search '{query[:80]}'")
        results = await loop.run_in_executor(_executor, _call)
        logger.info(f"RAG: found {len(results)} results")
        return results

    def shutdown(self):
        _executor.shutdown(wait=True)
        logger.info("RAG: executor shutdown")


current_dir = Path(__file__).resolve().parent  # src/services/
rag_db_path = current_dir.parents[2] / "rag" / "chroma_db"  # project_root/rag/chroma_db

rag_wrapper = RAGWrapper(db_path=str(rag_db_path))
