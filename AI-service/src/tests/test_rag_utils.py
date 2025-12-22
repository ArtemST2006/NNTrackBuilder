import logging

import pytest

from src.services.rag_utils import convert_rag_results_to_output


def test_convert_success():
    """Проверка успешной конвертации стандартных данных."""
    input_data = [
        {
            "name": "Красная площадь",
            "lat": "55.7558",
            "lon": "37.6173",
            "metadata": {"some": "info"}
        },
        {
            "name": "Эрмитаж",
            "metadata": {"lat": "59.9398", "lon": "30.3146"}
        }
    ]

    expected = [
        {"coordinates": "55.7558, 37.6173", "description": "Красная площадь"},
        {"coordinates": "59.9398, 30.3146", "description": "Эрмитаж"}
    ]

    assert convert_rag_results_to_output(input_data) == expected


def test_convert_missing_coordinates(caplog):
    """Проверка пропуска элементов без координат и записи в лог."""
    input_data = [
        {
            "name": "Место без координат",
            "metadata": {}
        },
        {
            "name": "Валидное место",
            "lat": "10.0",
            "lon": "20.0"
        }
    ]

    with caplog.at_level(logging.WARNING):
        result = convert_rag_results_to_output(input_data)

    # Должен остаться только 1 элемент
    assert len(result) == 1
    assert result[0]["description"] == "Валидное место"

    # Проверяем, что в логах появилось предупреждение
    assert "пропущен результат #1 без координат" in caplog.text


def test_convert_empty_list():
    """Проверка работы с пустым списком."""
    assert convert_rag_results_to_output([]) == []


def test_convert_priority_lat_lon():
    """Проверка, что lat/lon в корне имеют приоритет над теми, что в metadata."""
    input_data = [{
        "name": "Приоритет",
        "lat": "1.1",
        "lon": "2.2",
        "metadata": {"lat": "9.9", "lon": "8.8"}
    }]

    result = convert_rag_results_to_output(input_data)
    assert result[0]["coordinates"] == "1.1, 2.2"


@pytest.mark.parametrize("invalid_item", [
    {"name": "Нет долготы", "lat": "55.0"},
    {"name": "Нет широты", "lon": "37.0"},
    {"name": "Пусто", "metadata": None},
])
def test_convert_partial_data(invalid_item):
    """Параметризованный тест для разных вариантов неполных данных."""
    result = convert_rag_results_to_output([invalid_item])
    assert result == []
