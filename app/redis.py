import redis.asyncio as aioredis
from redis.asyncio import Redis

from app.config import settings

# Глобальная переменная для хранения клиента
redis_client: Redis | None = None

async def invalidate_project_tasks_cache(redis: Redis, project_id: int) -> None:
    """Удаляет все закэшированные страницы задач для конкретного проекта."""
    # Ищем все ключи, соответствующие шаблону проекта
    pattern = f"tasks:project:{project_id}:*"
    keys = await redis.keys(pattern)

    # Если найден хотя бы один ключ — удаляем пачкой за один вызов
    if keys:
        await redis.delete(*keys)

        
async def init_redis() -> Redis:
    """Инициализирует пул соединений и клиента Redis при старте приложения."""
    global redis_client

    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return redis_client


async def close_redis() -> None:
    """Корректно закрывает соединения с Redis при завершении работы сервера."""
    global redis_client
    if redis_client:
        await redis_client.aclose()


async def get_redis() -> Redis:
    """Dependency для внедрения redis_client в эндпоинты FastAPI через Depends()."""
    if redis_client is None:
        raise RuntimeError("Redis client is not initialized")
    return redis_client