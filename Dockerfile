# 1. Базовый легковесный образ Python
FROM python:3.12-slim-bookworm

# 2. Устанавливаем uv напрямую из официального образа
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 3. Настройка окружения
ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# 4. Копируем файлы зависимостей.
COPY pyproject.toml uv.lock ./

# 5. Устанавливаем только внешние зависимости без сборки самого проекта
RUN uv sync --frozen --no-install-project --no-dev

# 6. Копируем исходный код и миграции
COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic

# 7. Добавляем виртуальное окружение uv в PATH
ENV PATH="/app/.venv/bin:$PATH"

# 8. Порт FastAPI
EXPOSE 8000

# 9. Старт приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]