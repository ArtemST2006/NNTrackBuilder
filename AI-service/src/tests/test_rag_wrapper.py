# tests/test_rag_wrapper.py
import pytest
import time

import asyncio

if __package__ in (None, ""):
    import os
    import sys
    # Поднимаемся: файл -> tests -> src -> AI-service (корень)
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

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

    n = 1000

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