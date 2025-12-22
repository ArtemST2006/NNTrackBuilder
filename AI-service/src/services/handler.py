import logging
import subprocess
from typing import Dict, Any

from src.services.rag_wrapper import rag_wrapper
from src.services.rag_utils import convert_rag_results_to_output
from src.services.gigachat_service import GigachatService

logger = logging.getLogger(__name__)

gigachat = GigachatService()


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

    lat, lon = 56.314916, 43.980943
    if cords:
        try:
            coords = cords.split(", ")
            lat, lon = float(coords[0]), float(coords[1])
        except Exception as e:
            print(f"Ошибка парсинга координат: {e}")

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
        rag_results = await rag_wrapper.search_raw(query=query, user_lat=lat, user_lon=lon)

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
        route_json["output"].insert(0, {
            "coordinates": f"{lat}, {lon}",
            "description": "Мое местоположение"
        })

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
