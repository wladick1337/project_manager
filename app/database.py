import os
from collections.abc import AsyncGenerator

from app.schemas1.pagination import PaginationParams

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

load_dotenv()

# Получаем строку подключения
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment variables")

# Создаём асинхронный движок
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Поставь True, если нужно смотреть сырые SQL-запросы в консоли
    future=True,
)

# Фабрика асинхронных сессий
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Критически важный флаг для async
)


class Base(DeclarativeBase):
    pass


# Dependency для FastAPI роутеров
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def paginate(
    db: AsyncSession,
    query: Select,
    params: PaginationParams,
) -> tuple[list, int]:
    """Выполняет подсчет total и забирает нужный срез записей."""

    count_subquery = query.order_by(None).subquery()
    count_query = select(func.count()).select_from(count_subquery)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    paginated_query = query.offset(params.offset).limit(params.size)
    
    data_result = await db.execute(paginated_query)
    items = list(data_result.scalars().all())

    return items, total