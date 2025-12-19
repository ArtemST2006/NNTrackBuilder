# src/services/rag_utils.py

from typing import List, Dict, Any


def convert_rag_results_to_output(results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Преобразует результаты HybridSearcher в формат:

    [
      {"coordinates": "55.7558, 37.6173", "description": "Красная площадь, Москва"},
      ...
    ]
    """

    points: List[Dict[str, str]] = []

    for item in results:
        meta = item.get("metadata", {}) or {}

        lat = meta.get("lat")
        lon = meta.get("lon")

        if lat is None or lon is None:
            # если нет координат — пропускаем
            continue

        coordinates = f"{lat}, {lon}"

        name = meta.get("name") or item.get("name") or "Неизвестное место"
        city = meta.get("city")
        address = meta.get("address")

        parts = [name]
        if city:
            parts.append(city)
        if address:
            parts.append(address)

        description = ", ".join(parts)

        points.append(
            {
                "coordinates": coordinates,
                "description": description,
            }
        )

    return points
