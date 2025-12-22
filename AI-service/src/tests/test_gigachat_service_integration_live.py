import pytest

from src.config import GIGACHAT_CREDENTIALS
from src.services.gigachat_service import GigachatService

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_build_route_live_api():
    creds = GIGACHAT_CREDENTIALS


    if not creds:
        pytest.skip("Нет GIGACHAT_CREDENTIALS в env — пропускаем live-интеграционный тест.")

    service = GigachatService()

    points = [
        {"coordinates": "55.7558, 37.6173", "description": "Красная площадь, Москва"},
        {"coordinates": "55.7520, 37.6175", "description": "Московский Кремль"},
        {"coordinates": "59.9343, 30.3351", "description": "Эрмитаж, Санкт-Петербург"},
    ]

    result = await service.build_route(
        points,
        user_id=42,
        task_id="it-live-001",
        city_hint="Россия, в основном Москва и Санкт-Петербург",
    )

    print(result)
    # базовые проверки формы
    assert result["user_id"] == 42
    assert result["task_id"] == "it-live-001"
    assert isinstance(result["output"], list)
    assert isinstance(result["description"], str)
    assert isinstance(result["advice"], str)

    # time/long — допускаем int или float (некоторые модели могут отдать 2 вместо 2.0)
    assert isinstance(result["time"], (int, float))
    assert isinstance(result["long"], (int, float))

    # проверка, что output не содержит “левых” точек
    allowed = {(p["coordinates"], p["description"]) for p in points}
    for item in result["output"]:
        assert (item["coordinates"], item["description"]) in allowed
