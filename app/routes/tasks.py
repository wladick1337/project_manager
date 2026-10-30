from fastapi import APIRouter, Depends, status, HTTPException

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db
from app.schemas import TaskPublic, TaskUpdate, TaskCreate
from app.models import Project, User, Task
from app.deps import get_current_user


router = APIRouter(tags=["tasks"])

@router.post(
    "/projects/{project_id}/tasks",
    status_code=201, 
    response_model=TaskPublic
    )
def create_tasks(
    project_id: int, 
    task_data: TaskCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user),
):

    result = db.execute(select(Project).where(Project.id == project_id))

    project = result.scalars().first()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    task = Task(
        title = task_data.title,
        description = task_data.description,
        status = task_data.status,
        priority = task_data.priority,
        project_id=project.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get(
    "/projects/{project_id}/tasks", 
    response_model=list[TaskPublic]
    )
def get_tasks(
    project_id: int,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user),
):

    result = db.execute(select(Project).where(Project.id == project_id))

    project = result.scalars().first()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    tasks = db.execute(select(Task).where(Task.project_id == project_id)).scalars().all()

    return tasks

@router.get(
    "/tasks/{task_id}",
    response_model=TaskPublic
)
def get_task(
    task_id: int,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user),
):
    result = db.execute(select(Task).where(Task.id == task_id))

    task = result.scalars().first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    return task


@router.patch(
    "/tasks/{task_id}",
    response_model=TaskPublic,
)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user),
):
    result = db.execute(select(Task).where(Task.id == task_id))

    task = result.scalars().first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    update_data = task_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)
    return task


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user), 
):
    result = db.execute(select(Task).where(Task.id == task_id))

    task = result.scalars().first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    db.delete(task)
    db.commit()
    return None