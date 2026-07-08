from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from typing import Optional

from app.core.database import get_session
from app.models.schema import User, UserRole
from app.core.security import get_password_hash, verify_password

router = APIRouter(prefix="/auth", include_in_schema=False)
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="auth/login.html", context={"request": request})

@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session)
):
    user = session.exec(select(User).where(User.email == email)).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            request=request,
            name="auth/login.html", 
            context={"request": request, "error": "Invalid email or password"}
        )
    
    request.session["user_id"] = user.id
    return RedirectResponse(url="/ui/dashboard", status_code=303)

@router.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse(request=request, name="auth/signup.html", context={"request": request})

@router.post("/signup")
def signup(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    session: Session = Depends(get_session)
):
    if password != confirm_password:
        return templates.TemplateResponse(
            request=request,
            name="auth/signup.html", 
            context={"request": request, "error": "Passwords do not match"}
        )
    
    existing_user = session.exec(select(User).where(User.email == email)).first()
    if existing_user:
        return templates.TemplateResponse(
            request=request,
            name="auth/signup.html", 
            context={"request": request, "error": "Email is already registered"}
        )
    
    # Check if this is the first user
    user_count = len(session.exec(select(User.id)).all())
    role = UserRole.admin if user_count == 0 else UserRole.client
    
    new_user = User(
        email=email,
        full_name=full_name,
        hashed_password=get_password_hash(password),
        role=role
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    request.session["user_id"] = new_user.id
    return RedirectResponse(url="/ui/dashboard", status_code=303)

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/auth/login", status_code=303)
