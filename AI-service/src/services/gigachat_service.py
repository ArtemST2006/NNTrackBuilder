from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple
import json
import logging
import time
import re

from gigachat import GigaChat
from src.config import (
    GIGACHAT_CREDENTIALS,
    GIGACHAT_SCOPE,
    GIGACHAT_MODEL,
    GIGACHAT_VERIFY_SSL_CERTS,
)

logger = logging.getLogger(__name__)


class GigachatService:
    SYSTEM_INSTRUCTION = (
        "Ты — помощник по планированию маршрутов по городу.\n"
        "Тебе даётся список локаций, каждая локация описана координатами и текстовым описанием.\n"
        "Нужно:\n"
        "1. Составить оптимальный маршрут, выбирая те места, которые расположены "
        "   относительно близко друг к другу (примерно один район/часть города).\n"
        "2. Разрешается выбросить часть точек, если они сильно выбиваются по расположению.\n"
        "3. Сохраняй исходные значения полей coordinates и description без изменений.\n"
        "4. Вернуть СТРОГО один JSON-объект следующей структуры (без лишнего текста вокруг):\n"
        "{\n"
        "  \"user_id\": <целое число>,\n"
        "  \"task_id\": \"<строка, которую передал пользователь>\",\n"
        "  \"output\": [\n"
        "    {\n"
        "      \"coordinates\": \"55.7558, 37.6173\",\n"
        "      \"description\": \"Красная площадь, Москва\"\n"
        "    }\n"
        "  ],\n"
        "  \"description\": \"Красивая связная фраза/абзац, описывающие маршрут и атмосферу посещения мест (по-русски)\",\n"
        "  \"time\": <число с плавающей точкой, примерная длительность маршрута в часах>,\n"
        "  \"long\": <число с плавающей точкой, примерная длина маршрута в километрах>,\n"
        "  \"advice\": \"Короткий совет или пожелание путешественнику (по-русски)\"\n"
        "}\n"
        "5. Не добавляй никаких комментариев, пояснений или текста за пределами JSON.\n"
    )
    REPAIR_INSTRUCTION = (
        "Ты — валидатор JSON.\n"
        "Исправь синтаксис JSON без изменения смысла, структуры и значений.\n"
        "Верни СТРОГО один JSON-объект без любого дополнительного текста.\n"
    )

    def __init__(self) -> None:
        if not GIGACHAT_CREDENTIALS:
            raise ValueError("GIGACHAT_CREDENTIALS пуст. Укажи Authorization Key в env.")

        # Важно: не держим один и тот же клиент как self._giga и не шарим его между параллельными запросами.
        # Создаём клиента на запрос (ниже), это проще и безопаснее в async.
        logger.debug(
            "GigachatService настроен: model=%s, scope=%s, verify_ssl=%s",
            GIGACHAT_MODEL,
            GIGACHAT_SCOPE,
            GIGACHAT_VERIFY_SSL_CERTS,
        )

    def _build_user_prompt(
        self,
        points: List[Dict[str, str]],
        user_id: int,
        task_id: str,
        city_hint: Optional[str] = None,
    ) -> str:
        points_block = "\n".join(
            f"- coordinates: {p.get('coordinates')}, description: {p.get('description')}"
            for p in points
        )

        city_part = (
            f"Подсказка по городу/региону: {city_hint}.\n"
            if city_hint
            else "Город/регион явно не указан, оценивай близость по описаниям и координатам.\n"
        )

        return (
            "Ниже дан список точек, которые Пользователь хотел бы посетить.\n"
            f"{city_part}"
            "Твоя задача:\n"
            "- Выбрать из них подмножество точек так, чтобы маршрут был компактным по расстоянию,\n"
            "  без крайних точек в разных концах города/страны.\n"
            "- Вернуть точки в порядке посещения.\n"
            "- НЕЛЬЗЯ менять значения полей coordinates и description, только выбирать и упорядочивать.\n\n"
            f"user_id: {user_id}\n"
            f"task_id: {task_id}\n\n"
            "Список точек:\n"
            f"{points_block}\n\n"
            "Ответ должен быть СТРОГО в формате одного JSON-объекта, как описано в system-инструкции."
        )

    @staticmethod
    def _build_repair_prompt(raw_text: str) -> str:
        return (
            "Ниже дан JSON с ошибками. Исправь его и верни только валидный JSON:\n\n"
            f"{raw_text}"
        )

    async def _call_gigachat(self, messages: List[Dict[str, str]]) -> str:
        giga = GigaChat(
            credentials=GIGACHAT_CREDENTIALS,
            verify_ssl_certs=GIGACHAT_VERIFY_SSL_CERTS,
            scope=GIGACHAT_SCOPE,
            model=GIGACHAT_MODEL or None,
            async_mode=True,
        )

        async with giga as client:
            try:
                response = await client.achat(messages=messages)
            except TypeError:
                response = await client.achat({"messages": messages})
            except Exception as e:
                logger.exception("Ошибка при обращении к GigaChat: %s", e)
                raise

        raw_content = response.choices[0].message.content
        logger.debug("Ответ GigaChat (сырое содержимое): %s", raw_content)
        return raw_content

    @staticmethod
    def _extract_json_object(text: str) -> Dict[str, Any]:
        """
        Достаём JSON-объект:
        1) пробуем обычный json.loads
        2) если не вышло — убираем ```json ... ```
        3) если не вышло — вырезаем по внешним { ... }
        """
        text = text.strip()

        # 1) прямой парс
        try:
            obj = json.loads(text)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass

        # 2) code fence
        fenced = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE | re.MULTILINE).strip()
        if fenced != text:
            try:
                obj = json.loads(fenced)
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                pass

        # 3) вырез по скобкам
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            cut = text[start : end + 1]
            try:
                obj = json.loads(cut)
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError as e:
                raise ValueError(f"Не удалось распарсить JSON из ответа модели. Ошибка: {e}. Ответ: {text}") from e

        raise ValueError("Ответ модели не похож на JSON-объект. Ответ:\n" + text)

    @staticmethod
    def _validate_input_points(points: List[Dict[str, str]]) -> None:
        if not points:
            raise ValueError("Список points пуст — передайте хотя бы одну точку.")
        for i, p in enumerate(points, 1):
            if "coordinates" not in p or "description" not in p:
                raise ValueError(f"Элемент #{i} в points не содержит 'coordinates' или 'description': {p}")

    @staticmethod
    def _validate_and_normalize_output(
        data: Dict[str, Any],
        *,
        input_points: List[Dict[str, str]],
        user_id: int,
        task_id: str,
    ) -> Dict[str, Any]:
        required_root_keys = {"user_id", "task_id", "output", "description", "time", "long", "advice"}
        missing = required_root_keys - set(data.keys())
        if missing:
            raise ValueError(f"В ответе отсутствуют обязательные поля {missing}. Ответ: {data!r}")

        if not isinstance(data["output"], list):
            raise ValueError("'output' должен быть списком, получено: " + repr(data["output"]))

        # Жёсткая проверка: модель не имеет права придумывать/менять точки
        allowed: set[Tuple[str, str]] = {
            (p["coordinates"], p["description"]) for p in input_points
        }

        for i, item in enumerate(data["output"], 1):
            if not isinstance(item, dict):
                raise ValueError(f"Элемент output #{i} не является объектом: {repr(item)}")
            if "coordinates" not in item or "description" not in item:
                raise ValueError(f"Элемент output #{i} не содержит 'coordinates' или 'description': {repr(item)}")

            key = (item["coordinates"], item["description"])
            if key not in allowed:
                raise ValueError(
                    "Модель вернула точку, которой не было во входных данных, "
                    "или изменила coordinates/description: "
                    f"{item!r}"
                )

        # Подстраховка user_id / task_id
        data["user_id"] = user_id
        data["task_id"] = task_id

        return data

    async def build_route(
        self,
        points: List[Dict[str, str]],
        user_id: int,
        task_id: str,
        city_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        self._validate_input_points(points)

        logger.info(
            "Запуск построения маршрута: user_id=%s, task_id=%s, points_count=%s",
            user_id,
            task_id,
            len(points),
        )

        user_prompt = self._build_user_prompt(points, user_id, task_id, city_hint)

        messages = [
            {"role": "system", "content": self.SYSTEM_INSTRUCTION},
            {"role": "user", "content": user_prompt},
        ]

        start_time = time.monotonic()

        raw_content = await self._call_gigachat(messages)

        elapsed = time.monotonic() - start_time
        logger.info(
            "Запрос к GigaChat завершён: user_id=%s, task_id=%s, elapsed=%.3f сек",
            user_id,
            task_id,
            elapsed,
        )

        try:
            data = self._extract_json_object(raw_content)
        except ValueError as e:
            logger.warning(
                "JSON parse failed, retrying with repair prompt: %s", e
            )
            repair_messages = [
                {"role": "system", "content": self.REPAIR_INSTRUCTION},
                {"role": "user", "content": self._build_repair_prompt(raw_content)},
            ]
            repaired_content = await self._call_gigachat(repair_messages)
            data = self._extract_json_object(repaired_content)
        data = self._validate_and_normalize_output(
            data,
            input_points=points,
            user_id=user_id,
            task_id=task_id,
        )

        logger.info(
            "Маршрут успешно построен: user_id=%s, task_id=%s, точек_в_маршруте=%s",
            user_id,
            task_id,
            len(data["output"]),
        )
        return data
