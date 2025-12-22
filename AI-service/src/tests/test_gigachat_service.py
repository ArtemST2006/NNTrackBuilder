# tests/test_gigachat_service.py
import pytest
from src.services.gigachat_service import GigachatService


@pytest.mark.parametrize(
    "raw,expected",
    [
        ('{"a": 1}', {"a": 1}),
        ('```json\n{"a": 1}\n```', {"a": 1}),
        ('text before\n```json\n{"a": 1}\n```\ntext after', {"a": 1}),
        ('prefix {"a": 1} suffix', {"a": 1}),
    ],
)
def test_extract_json_object_ok(raw, expected):
    obj = GigachatService._extract_json_object(raw)
    assert obj == expected


def test_extract_json_object_fail():
    with pytest.raises(ValueError):
        GigachatService._extract_json_object("no json here")


def test_validate_input_points_ok():
    GigachatService._validate_input_points(
        [{"coordinates": "55.1, 37.2", "description": "A"}]
    )


@pytest.mark.parametrize(
    "points",
    [
        [],
        [{"coordinates": "55.1, 37.2"}],
        [{"description": "A"}],
        [{"coordinates": "55.1, 37.2", "description": "A"}, {"coordinates": "x"}],
    ],
)
def test_validate_input_points_fail(points):
    with pytest.raises(ValueError):
        GigachatService._validate_input_points(points)


def test_validate_and_normalize_output_ok():
    input_points = [
        {"coordinates": "55.7558, 37.6173", "description": "Красная площадь, Москва"},
        {"coordinates": "55.7520, 37.6175", "description": "Московский Кремль"},
    ]
    data = {
        "user_id": 999,
        "task_id": "wrong",
        "output": [
            {"coordinates": "55.7520, 37.6175", "description": "Московский Кремль"},
            {
                "coordinates": "55.7558, 37.6173",
                "description": "Красная площадь, Москва",
            },
        ],
        "description": "Маршрут по центру",
        "time": 3.5,
        "long": 4.2,
        "advice": "Надень удобную обувь",
    }

    normalized = GigachatService._validate_and_normalize_output(
        data,
        input_points=input_points,
        user_id=1,
        task_id="t-1",
    )
    assert normalized["user_id"] == 1
    assert normalized["task_id"] == "t-1"
    assert len(normalized["output"]) == 2


def test_validate_and_normalize_output_rejects_unknown_point():
    input_points = [
        {"coordinates": "55.7558, 37.6173", "description": "Красная площадь, Москва"},
    ]
    data = {
        "user_id": 1,
        "task_id": "t-1",
        "output": [{"coordinates": "0, 0", "description": "Луна"}],
        "description": "x",
        "time": 1.0,
        "long": 1.0,
        "advice": "x",
    }

    with pytest.raises(ValueError):
        GigachatService._validate_and_normalize_output(
            data,
            input_points=input_points,
            user_id=1,
            task_id="t-1",
        )


@pytest.mark.parametrize(
    "bad_data",
    [
        {},
        {"user_id": 1, "task_id": "t", "output": []},
        {
            "user_id": 1,
            "task_id": "t",
            "output": {},
            "description": "x",
            "time": 1.0,
            "long": 1.0,
            "advice": "x",
        },
        {
            "user_id": 1,
            "task_id": "t",
            "output": ["x"],
            "description": "x",
            "time": 1.0,
            "long": 1.0,
            "advice": "x",
        },
        {
            "user_id": 1,
            "task_id": "t",
            "output": [{"coordinates": "55, 37"}],
            "description": "x",
            "time": 1.0,
            "long": 1.0,
            "advice": "x",
        },
    ],
)
def test_validate_and_normalize_output_bad_shapes(bad_data):
    input_points = [{"coordinates": "55, 37", "description": "A"}]
    with pytest.raises(ValueError):
        GigachatService._validate_and_normalize_output(
            bad_data,
            input_points=input_points,
            user_id=1,
            task_id="t-1",
        )


@pytest.mark.asyncio
async def test_build_route_integration_mock(monkeypatch):
    """
    build_route без реального API: мокаем GigaChat в модуле сервиса.
    Также подставляем креды, чтобы __init__ сервиса не упал.
    """
    import src.services.gigachat_service as svc_mod

    # 1) подставляем креды (если сервис валидирует их в __init__)
    monkeypatch.setattr(svc_mod, "GIGACHAT_CREDENTIALS", "test-credentials")

    captured = {"messages": None}

    class FakeResponse:
        def __init__(self, content: str):
            self.choices = [
                type("C", (), {"message": type("M", (), {"content": content})()})()
            ]

    class FakeGigaChat:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def achat(self, *args, **kwargs):
            # Сервис сначала пробует achat(messages=messages)
            if "messages" in kwargs:
                captured["messages"] = kwargs["messages"]
            elif args and isinstance(args[0], dict) and "messages" in args[0]:
                captured["messages"] = args[0]["messages"]
            else:
                captured["messages"] = None

            return FakeResponse(
                """```json
                {
                  "user_id": 123,
                  "task_id": "xxx",
                  "output": [
                    {"coordinates": "55.7558, 37.6173", "description": "Красная площадь, Москва"}
                  ],
                  "description": "Прогулка по центру",
                  "time": 2.0,
                  "long": 3.0,
                  "advice": "Возьми воду"
                }
                ```"""
            )

    # 2) подменяем класс GigaChat в том модуле, где он используется
    monkeypatch.setattr(svc_mod, "GigaChat", FakeGigaChat)

    service = svc_mod.GigachatService()

    points = [
        {"coordinates": "55.7558, 37.6173", "description": "Красная площадь, Москва"},
        {"coordinates": "55.7520, 37.6175", "description": "Московский Кремль"},
    ]

    result = await service.build_route(
        points, user_id=1, task_id="t-1", city_hint="Москва"
    )

    assert result["user_id"] == 1
    assert result["task_id"] == "t-1"
    assert isinstance(result["output"], list)
    assert result["output"][0]["coordinates"] == "55.7558, 37.6173"
    assert result["output"][0]["description"] == "Красная площадь, Москва"

    # Доп. проверка: сервис реально передал messages в SDK
    assert captured["messages"] is not None
    assert captured["messages"][0]["role"] == "system"
    assert captured["messages"][1]["role"] == "user"
