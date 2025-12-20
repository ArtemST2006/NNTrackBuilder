import pytest


@pytest.mark.asyncio
async def test_handle_message_ok(monkeypatch):
    """
    Успешный сценарий:
    - RAG возвращает результаты
    - конвертер отдаёт points
    - gigachat.build_route возвращает валидный route_json
    """
    # ВАЖНО: импортируем модуль хендлера, чтобы мокать символы в НЁМ
    import src.services.handler as h

    data_in = {
        "depends": "profile",
        "task_id": "t-123",
        "user_id": 2,
        "profile": "",
        "input_data": {
            "category": ["музеи", "парки"],
            "time": 3.0,
            "cords": "55.7558, 37.6173",
            "place": "Москва",
        },
    }

    # --- моки ---
    async def fake_search_raw(query: str):
        assert isinstance(query, str)
        # проверим, что категории склеились в query
        assert "музеи" in query and "парки" in query
        return [{"id": "doc-1"}, {"id": "doc-2"}]

    def fake_convert(rag_results):
        assert rag_results == [{"id": "doc-1"}, {"id": "doc-2"}]
        return [
            {"coordinates": "55.7558, 37.6173", "description": "Красная площадь"},
            {"coordinates": "55.7520, 37.6175", "description": "Московский Кремль"},
        ]

    async def fake_build_route(points, user_id, task_id, city_hint=None):
        assert user_id == 2
        assert task_id == "t-123"
        assert city_hint == "Москва"  # place важнее cords
        # отдаём то, что ожидает хендлер
        return {
            "user_id": user_id,
            "task_id": task_id,
            "output": points,
            "description": "Маршрут по центру",
            "time": 2.5,
            "long": 4.0,
            "advice": "Удобная обувь",
        }

    # патчим зависимости в модуле хендлера
    monkeypatch.setattr(h.rag_wrapper, "search_raw", fake_search_raw)
    monkeypatch.setattr(h, "convert_rag_results_to_output", fake_convert)
    monkeypatch.setattr(h.gigachat, "build_route", fake_build_route)

    out = await h.handle_message(data_in)

    assert out["status"] == "ok"
    assert out["user_id"] == 2
    assert out["task_id"] == "t-123"
    assert isinstance(out["output"], list)
    assert out["description"]
    assert isinstance(out["time"], (int, float))
    assert isinstance(out["long"], (int, float))
    assert out["advice"]


@pytest.mark.asyncio
async def test_handle_message_rag_returns_empty(monkeypatch):
    """
    Если RAG ничего не нашёл -> status=error, error='Места не найдены'
    """
    import src.services.handler as h

    async def fake_search_raw(query: str):
        return []

    monkeypatch.setattr(h.rag_wrapper, "search_raw", fake_search_raw)

    out = await h.handle_message(
        {"task_id": "t-1", "user_id": 1, "input_data": {"category": ["x"]}}
    )

    assert out["status"] == "error"
    assert out["user_id"] == 1
    assert out["task_id"] == "t-1"
    assert out["error"] == "Места не найдены"


@pytest.mark.asyncio
async def test_handle_message_convert_returns_empty(monkeypatch):
    """
    Если конвертер не смог сделать points -> status=error
    """
    import src.services.handler as h  # <- поменяй на свой реальный путь модуля

    async def fake_search_raw(query: str):
        return [{"id": "doc-1"}]

    def fake_convert(rag_results):
        return []  # имитируем отсутствие координат/точек

    monkeypatch.setattr(h.rag_wrapper, "search_raw", fake_search_raw)
    monkeypatch.setattr(h, "convert_rag_results_to_output", fake_convert)

    out = await h.handle_message({"task_id": "t-2", "user_id": 2, "input_data": {}})

    assert out["status"] == "error"
    assert out["error"] == "Не удалось получить точки с координатами"


@pytest.mark.asyncio
async def test_handle_message_exception_in_gigachat(monkeypatch):
    """
    Если gigachat.build_route падает -> status=error + текст ошибки
    """
    import src.services.handler as h  # <- поменяй на свой реальный путь модуля

    async def fake_search_raw(query: str):
        return [{"id": "doc-1"}]

    def fake_convert(rag_results):
        return [{"coordinates": "55, 37", "description": "A"}]

    async def fake_build_route(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(h.rag_wrapper, "search_raw", fake_search_raw)
    monkeypatch.setattr(h, "convert_rag_results_to_output", fake_convert)
    monkeypatch.setattr(h.gigachat, "build_route", fake_build_route)

    out = await h.handle_message({"task_id": "t-3", "user_id": 3, "input_data": {}})

    assert out["status"] == "error"
    assert out["error"] == "boom"


@pytest.mark.asyncio
async def test_handle_message_city_hint_falls_back_to_cords(monkeypatch):
    """
    Если place пустой, city_hint должен быть cords.
    """
    import src.services.handler as h  # <- поменяй на свой реальный путь модуля

    async def fake_search_raw(query: str):
        return [{"id": "doc-1"}]

    def fake_convert(rag_results):
        return [{"coordinates": "55, 37", "description": "A"}]

    async def fake_build_route(points, user_id, task_id, city_hint=None):
        assert city_hint == "10, 20"
        return {
            "user_id": user_id,
            "task_id": task_id,
            "output": points,
            "description": "x",
            "time": 1.0,
            "long": 1.0,
            "advice": "x",
        }

    monkeypatch.setattr(h.rag_wrapper, "search_raw", fake_search_raw)
    monkeypatch.setattr(h, "convert_rag_results_to_output", fake_convert)
    monkeypatch.setattr(h.gigachat, "build_route", fake_build_route)

    out = await h.handle_message(
        {
            "task_id": "t-4",
            "user_id": 4,
            "input_data": {"place": "", "cords": "10, 20", "category": []},
        }
    )

    assert out["status"] == "ok"
    assert out["task_id"] == "t-4"
