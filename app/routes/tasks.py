import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db, paginate
from app.deps import get_current_user
from app.models import Project, Task, TaskPriority, TaskStatus, User
from app.redis import get_redis, invalidate_project_tasks_cache
from app.schemas import TaskCreate, TaskPublic, TaskUpdate
from app.schemas1.pagination import Page, PaginationParams

router = APIRouter(tags=["tasks"])


@router.post("/projects/{project_id}/tasks", status_code=201, response_model=TaskPublic)
async def create_tasks(
    project_id: int,
    task_data: TaskCreate,
    redis: Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    result = await db.execute(select(Project).where(Project.id == project_id))

    project = result.scalars().first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    task = Task(
        title=task_data.title,
        description=task_data.description,
        status=task_data.status,
        priority=task_data.priority,
        project_id=project.id,
    )

    db.add(task)
    await db.commit()
    await db.refresh(task)

    await invalidate_project_tasks_cache(redis, project_id)

    return task


@router.get("/projects/{project_id}/tasks", response_model=Page[TaskPublic])
async def get_tasks(
    project_id: int,
    params: PaginationParams = Depends(),
    task_status: TaskStatus | None = Query(default=None, alias="status"),
    priority: TaskPriority | None = Query(default=None),
    redis: Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Проверяем существование проекта и права доступа
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    cache_key = f"tasks:project:{project_id}:p:{params.page}:s:{params.size}:st:{task_status}:pr:{priority}"

    cached_data = await redis.get(cache_key)

    # Если ключ найден в Redis — возвращаем распарсенный JSON
    if cached_data:
        # json.loads превращает строку обратно в dict
        return json.loads(cached_data)
    # 2. Формируем базовый запрос выборки задач проекта

    query = select(Task).where(Task.project_id == project_id).order_by(Task.id)

    # 3. Применяем фильтры (если клиент их передал)
    if task_status:
        query = query.where(Task.status == task_status)
    if priority:
        query = query.where(Task.priority == priority)

    # 4. Делегируем подсчет total и нарезку limit/offset нашей функции
    items, total = await paginate(db, query, params)

    # Превращаем ORM-модели SQLAlchemy в Pydantic-схемы TaskPublic
    task_items = [TaskPublic.model_validate(item) for item in items]
    page_response = Page.create(items=task_items, total=total, params=params)

    # Теперь page_response состоит из валидных Pydantic-моделей и сериализуется без ошибок
    await redis.set(
        cache_key,
        page_response.model_dump_json(),
        ex=60,
    )

    return page_response


@router.get("/tasks/{task_id}", response_model=TaskPublic)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Task).options(joinedload(Task.project)).where(Task.id == task_id)
    result = await db.execute(query)
    task = result.scalars().first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    if task.project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    return task


@router.patch(
    "/tasks/{task_id}",
    response_model=TaskPublic,
)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    redis: Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Task).options(joinedload(Task.project)).where(Task.id == task_id)
    result = await db.execute(query)
    task = result.scalars().first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    if task.project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    update_data = task_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    await db.commit()
    await db.refresh(task)

    await invalidate_project_tasks_cache(redis, task.project_id)

    return task


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_task(
    task_id: int,
    redis: Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Task).options(joinedload(Task.project)).where(Task.id == task_id)
    result = await db.execute(query)
    task = result.scalars().first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    if task.project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    project_id = task.project_id

    await db.delete(task)
    await db.commit()

    await invalidate_project_tasks_cache(redis, project_id)

    return None
