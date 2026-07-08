from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from app.core.database import get_session
from app.models.schema import Requirement, ProjectGroup, User
from app.api.schemas import RequirementCreate

router = APIRouter(prefix="/projects", tags=["Requirements"])

@router.post("/{project_id}/requirements", status_code=status.HTTP_201_CREATED)
def create_requirement(project_id: int, req: RequirementCreate, session: Session = Depends(get_session)):
    project = session.get(ProjectGroup, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    creator = session.get(User, req.created_by)
    if not creator:
        raise HTTPException(status_code=404, detail="Creator user not found")
        
    if req.owner_id:
        owner = session.get(User, req.owner_id)
        if not owner:
            raise HTTPException(status_code=404, detail="Owner user not found")

    db_req = Requirement(
        project_id=project_id,
        title=req.title,
        description=req.description,
        module=req.module,
        priority=req.priority,
        acceptance_criteria=req.acceptance_criteria,
        due_date=req.due_date,
        created_by=req.created_by,
        owner_id=req.owner_id,
        complexity=req.complexity,
        business_value=req.business_value,
        estimated_effort_days=req.estimated_effort_days,
        ai_suggested_priority=req.ai_suggested_priority,
        ai_confidence=req.ai_confidence,
        ai_low_probability=req.ai_low_probability,
        ai_medium_probability=req.ai_medium_probability,
        ai_high_probability=req.ai_high_probability,
        priority_overridden=(req.priority.value != req.ai_suggested_priority.lower()) if req.ai_suggested_priority else False,
        suggested_effort_min_days=req.suggested_effort_min_days,
        suggested_effort_max_days=req.suggested_effort_max_days,
        suggested_effort_recommended_days=req.suggested_effort_recommended_days,
        suggested_effort_reason=req.suggested_effort_reason,
        effort_overridden=req.effort_overridden
    )
    session.add(db_req)
    session.commit()
    session.refresh(db_req)
    return db_req

@router.get("/{project_id}/requirements")
def list_requirements(project_id: int, session: Session = Depends(get_session)):
    project = session.get(ProjectGroup, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    reqs = session.exec(select(Requirement).where(Requirement.project_id == project_id)).all()
    return reqs
