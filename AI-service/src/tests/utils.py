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
            "category": "sightseeing",
        },
        "distance": 0.05,
        "base_score": 0.9523809523809523,
        "bm25_score": 1.0,
        "final_score": 0.975,
        "tags": ["история", "архитектура", "центр"],
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
            "lon": 37.6011,
        },
        "distance": None,
        "base_score": 0.0,
        "bm25_score": 0.85,
        "final_score": 0.425,
        "tags": ["парк", "отдых"],
    },
]


def _parse_coords(value):
    if not value:
        return None, None
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        parts = value[:2]
    elif isinstance(value, str):
        parts = value.split(",")
    else:
        return None, None

    if len(parts) < 2:
        return None, None

    try:
        lat = float(str(parts[0]).strip().replace(",", "."))
        lon = float(str(parts[1]).strip().replace(",", "."))
        return lat, lon
    except ValueError:
        return None, None
