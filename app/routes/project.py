from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models import Project, User
from app.schemas import ProjectCreate, ProjectPublic, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post(
    "",
    response_model=ProjectPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_projects(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    project = Project(
        title=project_data.title,
        description=project_data.description,
        owner_id=current_user.id,
    )

    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get(
    "",
    response_model=list[ProjectPublic],
)
async def get_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Project).where(Project.owner_id == current_user.id)
    result = await db.execute(query)
    projects = result.scalars().all()
    return projects


@router.get(
    "/{project_id}",
    response_model=ProjectPublic,
)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
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

    return project


@router.patch(
    "/{project_id}",
    response_model=ProjectPublic,
)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
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

    update_data = project_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)

    await db.commit()
    await db.refresh(project)
    return project


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
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

    await db.delete(project)
    await db.commit()
    return None
