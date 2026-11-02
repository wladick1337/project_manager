import os
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

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
