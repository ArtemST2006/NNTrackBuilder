from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def convert_rag_results_to_output(results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Преобразует результаты HybridSearcher в формат:

    [
      {"coordinates": "55.7558, 37.6173", "description": "Красная площадь, Москва"},
    ]
    """

    points: List[Dict[str, str]] = []

    for idx, item in enumerate(results, start=1):
        """
            ожидаемая структура item:
            {
                "name": ...,
                "final_score": ...,
                "metadata": {...},
                "lat": ... (опционально),
                "lon": ... (опционально),
                "distance": ...
            }
        """

        name = item.get("name")
        meta = item.get("metadata") or {}
        lat = item.get("lat", meta.get("lat"))
        lon = item.get("lon", meta.get("lon"))

        if lat is None or lon is None:
            logger.warning(
                "RAG: пропущен результат #%s без координат: name=%r, lat=%r, lon=%r, metadata_keys=%s",
                idx,
                name,
                lat,
                lon,
                list(meta.keys()),
            )
            continue

        coordinates = f"{lat}, {lon}"

        points.append(
            {
                "coordinates": coordinates,
                "description": name,
            }
        )

    logger.info(
        "RAG: конвертировано %s точек из %s входных результатов",
        len(points),
        len(results),
    )

    return points
