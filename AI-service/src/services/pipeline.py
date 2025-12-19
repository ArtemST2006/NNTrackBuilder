import logging
import time
from typing import Dict, Any

from src.services.rag_wrapper import rag_wrapper
from src.services.rag_utils import convert_rag_results_to_output

logger = logging.getLogger(__name__)


class AIPipeline:
    async def process_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Вход:
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
        profile = data.get("profile") or ""
        depends = data.get("depends") or ""

        start = time.time()

        try:
            # 1. Формируем query для RAG
            # Логика простая: если есть profile — берём его, если нет — place,
            # иначе собираем текст из категорий.
            if profile:
                query = profile
            elif place:
                query = place
            else:
                query = " ".join(categories) or "интересные места для прогулки"

            logger.info(
                f"Pipeline: user_id={user_id}, task_id={task_id}, query='{query[:80]}'"
            )

            # 2. RAG — ищем места
            rag_results = await rag_wrapper.search_places(
                query=query,
                categories=categories,
                time_hours=time_hours,
                cords=cords,
                place=place,
                n_results=5,
            )

            if not rag_results:
                return self._error_response(user_id, task_id, "Места не найдены")

            # 3. Преобразуем в формат output
            points = convert_rag_results_to_output(rag_results)
            if not points:
                return self._error_response(
                    user_id, task_id, "Не удалось получить точки с координатами"
                )

            # 4. Пока без GigaChat — просто отправляем точки и базовые поля
            elapsed = time.time() - start
            logger.info(
                f"Pipeline: success for task_id={task_id} in {elapsed:.2f}s, {len(points)} points"
            )

            return {
                "user_id": user_id,
                "task_id": task_id,
                "status": "ok",
                "output": points,
                "description": "Маршрут по найденным местам",  # потом заменишь GigaChat'ом
                "time": time_hours,
                "long": len(points) * 2.5,  # грубая заглушка, километры
                "advice": "Возьмите с собой удобную обувь",
            }

        except Exception as e:
            logger.exception(f"Pipeline error for task_id={task_id}")
            return self._error_response(user_id, task_id, str(e))

    def _error_response(
        self, user_id, task_id, error_msg: str | None = None
    ) -> Dict[str, Any]:
        resp: Dict[str, Any] = {
            "user_id": user_id,
            "task_id": task_id,
            "status": "error",
        }
        # можно логировать ошибку наверх
        if error_msg:
            resp["error"] = error_msg
        return resp


ai_pipeline = AIPipeline()
