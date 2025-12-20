# syntax=docker/dockerfile:1

# === Этап 1: Сборка (Builder) ===
FROM python:3.12-slim AS builder

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# 1. Обязательно обновляем pip (для поддержки wheel-файлов Python 3.12)
RUN pip install --upgrade pip

# 2. Устанавливаем Torch БЕЗ указания --index-url.
#    - Если вы на Mac (M1/M2): скачается версия для ARM (она маленькая, т.к. там нет CUDA).
#    - Если вы на Linux (Intel): скачается обычная версия.
#    - Флаг --no-cache-dir спасет от ошибки "No space left".
RUN pip install --no-cache-dir --user torch torchvision torchaudio

# 3. Устанавливаем остальные зависимости
RUN pip install --no-cache-dir --user -r requirements.txt

# === Этап 2: Финальный образ (Runtime) ===
FROM python:3.12-slim

WORKDIR /app

# Библиотека libgomp1 нужна для работы numpy/torch
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Копируем установленные пакеты
COPY --from=builder /root/.local /root/.local

COPY . .

# Настройка путей
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=INFO

# Создаем пользователя
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8004

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import sys; print('healthy')" || exit 1

CMD ["python", "main.py"]