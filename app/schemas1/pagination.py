import math

from fastapi import Query

from typing import Generic, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")

    
class PaginationParams:
    """Извлекает и валидирует query-параметры page и size из запроса."""

    def __init__(
        self,
        page: int = Query(default=1, ge=1),
        size: int = Query(default=20, ge=1, le=100),
    ):
        self.page = page
        self.size = size

        self.offset = (self.page - 1) * self.size


class Page(BaseModel, Generic[T]):
    """Универсальная схема ответа c метаданными пагинации."""

    items: list[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def create(cls, items: list[T], total: int, params: PaginationParams) -> "Page[T]":
        calculated_pages = math.ceil(total / params.size) if total > 0 else 1

        return cls(
            items=items,
            total=total,
            page=params.page,
            size=params.size,
            pages=calculated_pages,
        )