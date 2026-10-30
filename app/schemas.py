from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, EmailStr

from app.models import TaskPriority, TaskStatus

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str | None = None

class ProjectUpdate(BaseModel):
    title: str | None = None
    description: str | None = None

class ProjectPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None = None
    owner_id: int
    created_at: datetime


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str | None = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM

class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None

class TaskPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None = None
    status: TaskStatus
    priority:TaskPriority
    project_id: int
    created_at: datetime
