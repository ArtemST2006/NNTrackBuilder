import logging
from typing import Dict, Any

from src.services.rag_wrapper import rag_wrapper
from src.services.rag_utils import convert_rag_results_to_output
from src.services.gigachat_service import GigachatService

logger = logging.getLogger(__name__)

gigachat = GigachatService()

MOCK_SEARCH_RESULTS = [
    {
        "id": "101",
        "name": "Красная площадь",
        "text": "Главная площадь Москвы, расположенная в центре радиально-кольцевой планировки го...",
        "full_text": "Главная площадь Москвы, расположенная в центре радиально-кольцевой планировки города.",
        "metadata": {
            "name": "Красная площадь",
            "city": "Москва",
            "lat": 55.7558,
            "lon": 37.6173,
            "category": "sightseeing"
        },
        "distance": 0.05,
        "base_score": 0.9523809523809523,
        "bm25_score": 1.0,
        "final_score": 0.975,
        "tags": ["история", "архитектура", "центр"]
    },
    {
        "id": "202",
        "name": "Парк Горького",
        "text": "Центральный парк культуры и отдыха имени Максима Горького — парковая зона в Моск...",
        "full_text": "Центральный парк культуры и отдыха имени Максима Горького — парковая зона в Москве.",
        "metadata": {
            "name": "Парк Горького",
            "city": "Москва",
            "lat": 55.7282,
            "lon": 37.6011
        },
        "distance": None,
        "base_score": 0.0,
        "bm25_score": 0.85,
        "final_score": 0.425,
        "tags": ["парк", "отдых"]
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

    '''
    output
    {
          "user_id": user_id,
          "task_id": task_id,
          "status": "ok",
          "output": [
            {
              "coordinates": "56.328552, 44.003185",
              "description": "Кремль, Нижний Новгород"
            },
            {
              "coordinates": "56.323207, 44.009519",
              "description": "МТС Life hall, Нижний Новгород"
            },
            {
              "coordinates": "56.315617, 44.007783",
              "description": "Парк Кулибина, Нижний Новгород"
            }
          ],
          "description": "Тестовый маршрут созданный вручную",
          "time": 3.5,
          "long": 45.5,
          "advice": "Не забудьте зонтик"
        }
    '''

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
        rag_results = await rag_wrapper.search_raw(query=query)
        # rag_results = MOCK_SEARCH_RESULTS

        if not rag_results:
            return _error_response(user_id, task_id, "Места не найдены")

        # 3. RAG -> points
        points = convert_rag_results_to_output(rag_results)  # ломается
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
