import logging
from typing import Dict, Any

# from src.services.rag_wrapper import rag_wrapper
from src.services.rag_utils import convert_rag_results_to_output
from src.services.gigachat_service import GigachatService

logger = logging.getLogger(__name__)

gigachat = GigachatService()

MOCK_SEARCH_RESULTS = [
    {
        "id": "doc_123",
        "name": "Кофта утеплённая 'Зимняя сказка'",
        "text": "Утеплённая кофта для активного отдыха. Материал: флис + мембрана...",
        "full_text": "Утеплённая кофта для активного отдыха. Материал: флис + мембрана. Подходит для температур до -15°C. Ветро- и влагозащита. Карманы на молнии, регулируемый капюшон.",
        "metadata": {
            "category": "одежда",
            "price_range": "mid",
            "season": "winter",
            "city": "Москва",
            "semantic_tags": '["тепло", "поход", "зима"]'
        },
        "distance": 0.24,
        "base_score": 0.806,
        "bm25_score": 0.92,
        "lexical_score": 0.88,
        "final_score": 0.892,
        "tags": ["тепло", "поход", "зима"]
    },
    {
        "id": "doc_456",
        "name": "Термобельё Merino Pro",
        "text": "Термобельё из 100% мериносовой шерсти. Антибактериальное, не пахнет...",
        "full_text": "Термобельё из 100% мериносовой шерсти. Антибактериальное, не пахнет даже после 3 дней носки. Оптимальная температура использования: -20°C — +5°C.",
        "metadata": {
            "category": "одежда",
            "price_range": "high",
            "season": "winter",
            "city": "Москва",
            "semantic_tags": '["тепло", "долгий поход", "спорт"]'
        },
        "distance": 0.31,
        "base_score": 0.763,
        "bm25_score": 0.76,
        "lexical_score": 0.71,
        "final_score": 0.755,
        "tags": ["тепло", "долгий поход", "спорт"]
    },
    {
        "id": "doc_789",
        "name": "Туристический термос 1L Arctic",
        "text": "Сохраняет тепло 24 часа, холод — 48 часов. Ударопрочный корпус...",
        "full_text": "Сохраняет тепло 24 часа, холод — 48 часов. Ударопрочный корпус из нержавеющей стали. Подходит для походов и автотуризма. Совместим с фильтрами воды.",
        "metadata": {
            "category": "снаряжение",
            "price_range": "mid",
            "season": "all",
            "city": "Санкт-Петербург",
            "semantic_tags": '["поход", "выживание", "зима"]'
        },
        "distance": 0.48,
        "base_score": 0.676,
        "bm25_score": 0.54,
        "lexical_score": 0.62,
        "final_score": 0.648,
        "tags": ["поход", "выживание", "зима"]
    }
]


async def handle_message(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Вход (из Kafka):
    {
      "depends": "profile",
      "task_id": "...",
      "user_id": 2,
      "profile": "",
      "input_data": {
        "category": [...],
        "time": 3.0,
        "cords": "45.43534, 44.435436",
        "place": ""
      }
    }
    """

    user_id = data.get("user_id")
    task_id = data.get("task_id")

    input_data = data.get("input_data") or {}
    categories = input_data.get("category") or []
    time_hours = input_data.get("time") or 3.0
    cords = input_data.get("cords")
    place = input_data.get("place") or ""

    try:
        # 1. query для RAG
        query = " ".join(categories) or "интересные места"

        logger.info(
            "Handler: user_id=%s, task_id=%s, query='%s'",
            user_id,
            task_id,
            query[:80],
        )

        # 2. RAG
        # rag_results = await rag_wrapper.search_raw(query=query)
        rag_results = MOCK_SEARCH_RESULTS

        if not rag_results:
            return _error_response(user_id, task_id, "Места не найдены")

        # 3. RAG -> points
        points = convert_rag_results_to_output(rag_results)
        if not points:
            return _error_response(
                user_id, task_id, "Не удалось получить точки с координатами"
            )

        # 4. GigaChat через GigachatService
        city_hint = place or cords
        route_json = await gigachat.build_route(
            points=points,
            user_id=user_id,
            task_id=str(task_id),
            city_hint=city_hint,
        )

        # GigachatService уже возвращает:
        # { "user_id", "task_id", "output", "description", "time", "long", "advice" }
        route_json["status"] = "ok"

        # route_json = {
        #   "user_id": user_id,
        #   "task_id": task_id,
        #   "status": "ok",
        #   "output": [
        #     {
        #       "coordinates": "56.328552, 44.003185",
        #       "description": "Кремль, Нижний Новгород"
        #     },
        #     {
        #       "coordinates": "56.323207, 44.009519",
        #       "description": "МТС Life hall, Нижний Новгород"
        #     },
        #     {
        #       "coordinates": "56.315617, 44.007783",
        #       "description": "Парк Кулибина, Нижний Новгород"
        #     }
        #   ],
        #   "description": "Тестовый маршрут созданный вручную",
        #   "time": 3.5,
        #   "long": 45.5,
        #   "advice": "Не забудьте зонтик"
        # }

        return route_json

    except Exception as e:
        logger.exception("Handler error for task_id=%s", task_id)
        return _error_response(user_id, task_id, str(e))


def _error_response(user_id, task_id, msg: str | None = None) -> Dict[str, Any]:
    resp: Dict[str, Any] = {
        "user_id": user_id,
        "task_id": task_id,
        "status": "error",
    }
    if msg:
        resp["error"] = msg
    return resp
