# pyright: reportCallIssue=false
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from app.core.database import get_session
from app.models.schema import ProjectGroup, ProjectParticipant, User, UserRole
from app.api.schemas import ProjectCreate, ProjectRead, ParticipantAdd

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(project: ProjectCreate, session: Session = Depends(get_session)):
    # Check duplicate project code
    existing_project = session.exec(select(ProjectGroup).where(ProjectGroup.project_code == project.project_code)).first()
    if existing_project:
        raise HTTPException(status_code=400, detail="Project code already exists")
    
    # Check if created_by user exists
    user = session.get(User, project.created_by)
    if not user:
        raise HTTPException(status_code=404, detail="Creator user not found")

    db_project = ProjectGroup(
        project_code=project.project_code,
        name=project.name,
        description=project.description,
        created_by=project.created_by
    )
    session.add(db_project)
    session.commit()
    session.refresh(db_project)
    
    # Auto-add creator as participant with pm role
    participant = ProjectParticipant(
        project_id=db_project.id,
        user_id=db_project.created_by,
        role=UserRole.pm
    )
    session.add(participant)
    session.commit()
    
    return db_project

@router.get("/", response_model=List[ProjectRead])
def list_projects(session: Session = Depends(get_session)):
    return session.exec(select(ProjectGroup)).all()

@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, session: Session = Depends(get_session)):
    project = session.get(ProjectGroup, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.post("/{project_id}/participants")
def add_participant(project_id: int, participant: ParticipantAdd, session: Session = Depends(get_session)):
    project = session.get(ProjectGroup, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    user = session.get(User, participant.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Check if participant already exists
    existing = session.exec(
        select(ProjectParticipant)
        .where(ProjectParticipant.project_id == project_id)
        .where(ProjectParticipant.user_id == participant.user_id)
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="User is already a participant in this project")
        
    db_participant = ProjectParticipant(
        project_id=project_id,
        user_id=participant.user_id,
        role=participant.role
    )
    session.add(db_participant)
    session.commit()
    return {"status": "ok", "message": "Participant added"}
