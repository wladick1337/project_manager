from fastapi import APIRouter, Depends, status, HTTPException, Query

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db
from app.schemas import UserCreate, UserPublic
from app.models import User
from app.security import hash_password
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    )
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
        ):

    query = select(User).where(User.email == user.email)
    result = db.execute(query)
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    hashed = hash_password(user.password)
    new_user = User(email=user.email, hashed_password=hashed)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
