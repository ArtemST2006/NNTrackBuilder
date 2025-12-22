# tests/test_rag_wrapper.py
import pytest
import asyncio
import time

from watchfiles import awatch

from src.services.rag_wrapper import RAGWrapper

QUERIES = [
    "парки",
    "вкусно поесть",
    "история",
    "музей",
    "фоырдварфоывадол",
    "йух",
    "запрет",
    "Пушкин",
    "погулять с детьми",
    "фдыыдрва паррк"
]

rag = RAGWrapper()

@pytest.mark.asyncio
async def test_speed_tread_pool():
    query = "парки, музей, искусства, вкусно поесть"
    lat, lon = 56.314916, 43.980943

    n = 10_000

    # последовательно
    start = time.perf_counter()
    seq_results = [await rag.search_raw(query, lat, lon) for _ in range(n)]
    seq_duration = time.perf_counter() - start


    # параллельно
    start = time.perf_counter()
    par_results = await asyncio.gather(*(rag.search_raw(query, lat, lon) for _ in range(n)))
    par_duration = time.perf_counter() - start

    print(f"Sequential: {seq_duration:.4f} sec")
    print(f"Parallel:   {par_duration:.4f} sec")

    assert par_duration < seq_duration
