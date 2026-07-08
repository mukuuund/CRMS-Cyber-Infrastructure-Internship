
from fastapi import FastAPI, Depends, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
import os

from app.core.security import NotAuthenticated
from sqlmodel import Session, select
from app.core.database import get_session
import app.models  # to ensure models are loaded

from app.api.routers import users, projects, requirements, change_requests, ml
from app.frontend_routes import router as ui_router
from app.auth_routes import router as auth_router
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Change Request Management API")

app.include_router(users.router)
app.include_router(projects.router)
app.include_router(requirements.router)
app.include_router(change_requests.router)
app.include_router(ml.router)
app.include_router(ui_router)
app.include_router(auth_router)

# Add Session Middleware
session_secret = os.environ.get("SESSION_SECRET", "super-secret-dev-key-do-not-use-in-prod")
app.add_middleware(SessionMiddleware, secret_key=session_secret)

@app.exception_handler(NotAuthenticated)
async def not_authenticated_handler(request: Request, exc: NotAuthenticated):
    return RedirectResponse(url="/auth/login", status_code=303)

# Mount static files
import os
os.makedirs("app/static", exist_ok=True)
os.makedirs("app/templates", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Change Request Tracker API running"}

@app.get("/db-health")
def db_health(session: Session = Depends(get_session)):
    try:
        # Execute a simple query
        result = session.exec(select(1)).first()
        if result == 1:
            return {"status": "ok", "message": "Database is connected successfully"}
        return {"status": "error", "message": "Database connected but returned unexpected result"}
    except Exception as e:
        return {"status": "error", "message": f"Database connection failed: {str(e)}"}
