from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session, select
from typing import List
from app.core.database import get_session
from app.models.schema import User, UserRole
from app.api.schemas import UserCreate, UserRead
from app.core.security import get_password_hash

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, request: Request, session: Session = Depends(get_session)):
    # Check for duplicate email
    existing_user = session.exec(select(User).where(User.email == user.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    user_count = session.exec(select(User)).all()
    is_empty_db = len(user_count) == 0

    if user.role == UserRole.admin and not is_empty_db:
        user_id = request.session.get("user_id") if hasattr(request, "session") else None
        caller = session.get(User, user_id) if user_id else None
        if not caller or caller.role != UserRole.admin:
            raise HTTPException(status_code=403, detail="Only admins can create admin users.")
    
    db_user = User(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        full_name=user.full_name,
        role=user.role
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@router.get("/", response_model=List[UserRead])
def list_users(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return users
