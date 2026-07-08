from fastapi import APIRouter, Request, Depends, Form, Cookie, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select, col
from typing import Optional
from datetime import date, datetime, timedelta, timezone

from app.core.database import get_session
from app.models.schema import User, ProjectGroup, Requirement, ChangeRequest, Comment, ChangeApproval, ProjectParticipant
from app.models.schema import UserRole, ProjectStatus, RequirementPriority, ChangeRequestRiskLevel, ApprovalDecision, RequirementStatus, ChangeRequestStatus
from app.api.routers import projects as projects_api
from app.api.routers import requirements as reqs_api
from app.api.routers import change_requests as cr_api
from app.api.schemas import ProjectCreate, ParticipantAdd, RequirementCreate, ChangeRequestCreate, ApprovalDecisionCreate, CommentCreate

router = APIRouter(prefix="/ui", include_in_schema=False)
templates = Jinja2Templates(directory="app/templates")

from app.core.security import NotAuthenticated
from app.core.permissions import is_admin, is_project_participant, can_manage_project, can_create_project, can_change_global_roles, can_approve_requirement, can_close_project, can_approve_change_request
from app.core.activity import log_activity
from app.models.schema import ActivityLog

def get_current_user(request: Request, session: Session = Depends(get_session)) -> Optional[User]:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return session.get(User, user_id)

def require_current_user(current_user: Optional[User] = Depends(get_current_user)) -> User:
    if not current_user:
        raise NotAuthenticated()
    return current_user

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, session: Session = Depends(get_session), current_user: User = Depends(require_current_user)):
    users = session.exec(select(User)).all()
    current_user_id = current_user.id
    
    if current_user.role == UserRole.admin:
        user_projects = session.exec(select(ProjectGroup).order_by(col(ProjectGroup.created_at).desc())).all()
    else:
        user_projects = session.exec(
            select(ProjectGroup)
            .join(ProjectParticipant, col(ProjectParticipant.project_id) == col(ProjectGroup.id))
            .where(ProjectParticipant.user_id == current_user_id)
            .order_by(col(ProjectGroup.created_at).desc())
        ).all()
        
    project_ids = [p.id for p in user_projects]
    
    user_reqs = session.exec(
        select(Requirement)
        .where(col(Requirement.project_id).in_(project_ids))
    ).all() if project_ids else []
    
    user_crs = session.exec(
        select(ChangeRequest)
        .where(col(ChangeRequest.project_id).in_(project_ids))
    ).all() if project_ids else []
    
    # New metrics
    total_projects = len(user_projects)
    total_reqs = len(user_reqs)
    submitted_reqs = sum(1 for req in user_reqs if req.status == RequirementStatus.submitted)
    approved_reqs = sum(1 for req in user_reqs if req.status == RequirementStatus.approved)
    changes_requested_reqs = sum(1 for req in user_reqs if req.status == RequirementStatus.changes_requested)
    high_priority_reqs = sum(1 for req in user_reqs if req.priority in [RequirementPriority.high, RequirementPriority.critical])
    ai_overrides = sum(1 for req in user_reqs if req.priority_overridden)
    
    # 4. Last 5 User Actions (ActivityLog)
    my_actions = session.exec(
        select(ActivityLog)
        .where(ActivityLog.actor_id == current_user_id)
        .order_by(col(ActivityLog.created_at).desc())
        .limit(5)
    ).all()
    
    recent_actions = []
    for a in my_actions:
        p = session.get(ProjectGroup, a.project_id) if a.project_id else None
        link = "#"
        if a.requirement_id:
            link = f"/ui/requirements/{a.requirement_id}"
        elif a.project_id:
            link = f"/ui/projects/{a.project_id}"
        recent_actions.append({
            "text": a.message or f"Performed {a.action}",
            "project": p.name if p else "Unknown",
            "time": a.created_at,
            "link": link
        })
    
    # 5. Last 24 Hours Notifications
    last_24h = datetime.now(timezone.utc) - timedelta(hours=24)
    if current_user.role == UserRole.admin:
        recent_logs = session.exec(select(ActivityLog).where(ActivityLog.created_at >= last_24h).order_by(col(ActivityLog.created_at).desc())).all()
    else:
        recent_logs = []
        if project_ids:
            recent_logs = session.exec(
                select(ActivityLog)
                .where(col(ActivityLog.project_id).in_(project_ids))
                .where(ActivityLog.created_at >= last_24h)
                .order_by(col(ActivityLog.created_at).desc())
            ).all()
            
    notifications = []
    for a in recent_logs:
        notifications.append({
            "text": a.message or f"{a.action} occurred",
            "time": a.created_at
        })
    
    return templates.TemplateResponse(request=request, name="dashboard.html", context={
        "request": request,
        "users": users,
        "current_user": current_user,
        "total_projects": total_projects,
        "total_reqs": total_reqs,
        "submitted_reqs": submitted_reqs,
        "approved_reqs": approved_reqs,
        "changes_requested_reqs": changes_requested_reqs,
        "high_priority_reqs": high_priority_reqs,
        "ai_overrides": ai_overrides,
        "latest_projects": user_projects[:5],
        "recent_actions": recent_actions,
        "notifications": notifications
    })

@router.get("/projects", response_class=HTMLResponse)
def list_projects(request: Request, session: Session = Depends(get_session), current_user: User = Depends(require_current_user)):
    users = session.exec(select(User)).all()
    if current_user.role == UserRole.admin:
        all_projects = session.exec(select(ProjectGroup)).all()
    else:
        all_projects = session.exec(
            select(ProjectGroup)
            .join(ProjectParticipant, col(ProjectParticipant.project_id) == col(ProjectGroup.id))
            .where(ProjectParticipant.user_id == current_user.id)
            .order_by(col(ProjectGroup.created_at).desc())
        ).all()
    
    return templates.TemplateResponse(request=request, name="projects.html", context={
        "request": request, 
        "users": users,
        "current_user": current_user,
        "projects": all_projects,
        "UserRole": UserRole,
        "can_create": can_create_project(current_user)
    })

@router.post("/projects/create")
def create_project(
    project_code: str = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    if not can_create_project(current_user):
        raise HTTPException(status_code=403, detail="Not authorized to create projects")
        
    current_user_id = current_user.id
    assert current_user_id is not None
    proj_create = ProjectCreate(
        project_code=project_code,
        name=name,
        description=description,
        created_by=current_user_id
    )
    try:
        proj = projects_api.create_project(proj_create, session)
        assert proj.id is not None
        log_activity(
            session=session,
            project_id=proj.id,
            actor_id=current_user_id,
            action="project_created",
            message=f"Created project {proj.project_code}"
        )
        session.commit()
    except HTTPException:
        pass
    return RedirectResponse(url="/ui/projects", status_code=303)

@router.get("/projects/{project_id}", response_class=HTMLResponse)
def project_details(project_id: int, request: Request, session: Session = Depends(get_session), current_user: User = Depends(require_current_user)):
    users = session.exec(select(User)).all()
    project = session.get(ProjectGroup, project_id)
    if not project:
        raise HTTPException(status_code=404)
        
    participants = session.exec(
        select(ProjectParticipant, User)
        .join(User, col(ProjectParticipant.user_id) == col(User.id))
        .where(ProjectParticipant.project_id == project_id)
    ).all()
    
    requirements = session.exec(
        select(Requirement)
        .where(Requirement.project_id == project_id)
    ).all()
    
    change_requests = session.exec(
        select(ChangeRequest)
        .where(ChangeRequest.project_id == project_id)
    ).all()
    
    if not is_project_participant(current_user, project_id, session):
        raise HTTPException(status_code=403, detail="Not a participant in this project")
        
    can_manage = can_manage_project(current_user, project_id, session)
    can_approve = can_approve_requirement(current_user, project_id, session)
    can_close = can_close_project(current_user)
    is_project_editable = project.status == ProjectStatus.active
    
    # Get reviewer info for requirements
    reviewer_dict = {}
    for req in requirements:
        if req.reviewed_by_id:
            reviewer = session.get(User, req.reviewed_by_id)
            if reviewer:
                reviewer_dict[req.id] = reviewer.full_name
    
    return templates.TemplateResponse(request=request, name="project_details.html", context={
        "request": request,
        "users": users,
        "current_user": current_user,
        "project": project,
        "participants": participants,
        "requirements": requirements,
        "change_requests": change_requests,
        "UserRole": UserRole,
        "can_manage": can_manage,
        "can_approve": can_approve,
        "can_close": can_close,
        "is_project_editable": is_project_editable,
        "RequirementStatus": RequirementStatus,
        "ProjectStatus": ProjectStatus,
        "reviewer_dict": reviewer_dict
    })

@router.post("/projects/{project_id}/participants")
def add_participant(
    project_id: int,
    user_id: int = Form(...),
    role: str = Form(...),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    project = session.get(ProjectGroup, project_id)
    if not project or project.status != ProjectStatus.active:
        raise HTTPException(status_code=403, detail="Project is not active")

    if not can_manage_project(current_user, project_id, session):
        raise HTTPException(status_code=403, detail="Not authorized to manage participants")
        
    current_user_id = current_user.id
    assert current_user_id is not None
    part_add = ParticipantAdd(
        user_id=user_id,
        role=UserRole(role)
    )
    try:
        projects_api.add_participant(project_id, part_add, session)
        log_activity(
            session=session,
            project_id=project_id,
            actor_id=current_user_id,
            action="participant_added",
            message=f"Added user {user_id} with role {role}"
        )
        session.commit()
    except HTTPException:
        pass
    return RedirectResponse(url=f"/ui/projects/{project_id}", status_code=303)

@router.post("/projects/{project_id}/requirements")
def create_requirement(
    project_id: int,
    title: str = Form(...),
    description: str = Form(""),
    module: str = Form(""),
    priority: str = Form(...),
    complexity: Optional[str] = Form(None),
    business_value: Optional[str] = Form(None),
    estimated_effort_days: Optional[float] = Form(None),
    ai_suggested_priority: Optional[str] = Form(None),
    ai_confidence: Optional[float] = Form(None),
    ai_low_probability: Optional[float] = Form(None),
    ai_medium_probability: Optional[float] = Form(None),
    ai_high_probability: Optional[float] = Form(None),
    suggested_effort_min_days: Optional[float] = Form(None),
    suggested_effort_max_days: Optional[float] = Form(None),
    suggested_effort_recommended_days: Optional[float] = Form(None),
    suggested_effort_reason: Optional[str] = Form(None),
    owner_id: Optional[int] = Form(None),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    project = session.get(ProjectGroup, project_id)
    if not project or project.status != ProjectStatus.active:
        raise HTTPException(status_code=403, detail="Project is not active")

    if not is_project_participant(current_user, project_id, session):
        raise HTTPException(status_code=403, detail="Not a participant in this project")
        
    current_user_id = current_user.id
    assert current_user_id is not None
    
    effort_overridden = False
    if estimated_effort_days is not None and suggested_effort_recommended_days is not None:
        if float(estimated_effort_days) != float(suggested_effort_recommended_days):
            effort_overridden = True
            
    req_create = RequirementCreate(
        title=title,
        description=description,
        module=module,
        priority=RequirementPriority(priority),
        created_by=current_user_id,
        owner_id=owner_id,
        complexity=complexity,
        business_value=business_value,
        estimated_effort_days=estimated_effort_days,
        ai_suggested_priority=ai_suggested_priority,
        ai_confidence=ai_confidence,
        ai_low_probability=ai_low_probability,
        ai_medium_probability=ai_medium_probability,
        ai_high_probability=ai_high_probability,
        suggested_effort_min_days=suggested_effort_min_days,
        suggested_effort_max_days=suggested_effort_max_days,
        suggested_effort_recommended_days=suggested_effort_recommended_days,
        suggested_effort_reason=suggested_effort_reason,
        effort_overridden=effort_overridden
    )
    try:
        req_res = reqs_api.create_requirement(project_id, req_create, session)
        log_activity(
            session=session,
            project_id=project_id,
            requirement_id=req_res.id,
            actor_id=current_user_id,
            action="requirement_created",
            message=f"Created requirement: {req_res.title}"
        )
        
        if ai_suggested_priority:
            conf_pct = round(ai_confidence * 100, 1) if ai_confidence else 0
            log_activity(
                session=session,
                project_id=project_id,
                requirement_id=req_res.id,
                actor_id=current_user_id,
                action="ai_priority_suggested",
                message=f"AI suggested {ai_suggested_priority.upper()} priority with {conf_pct}% confidence."
            )
            
            if priority.lower() == ai_suggested_priority.lower():
                log_activity(
                    session=session,
                    project_id=project_id,
                    requirement_id=req_res.id,
                    actor_id=current_user_id,
                    action="priority_confirmed",
                    message=f"Priority confirmed as {priority.upper()}."
                )
            else:
                log_activity(
                    session=session,
                    project_id=project_id,
                    requirement_id=req_res.id,
                    actor_id=current_user_id,
                    action="priority_overridden",
                    message=f"Priority overridden from {ai_suggested_priority.upper()} to {priority.upper()}."
                )
                
        if suggested_effort_recommended_days:
            log_activity(
                session=session,
                project_id=project_id,
                requirement_id=req_res.id,
                actor_id=current_user_id,
                action="effort_range_suggested",
                message=f"Effort range suggested: {suggested_effort_min_days}-{suggested_effort_max_days} days (recommended: {suggested_effort_recommended_days})."
            )
            
            if not effort_overridden:
                log_activity(
                    session=session,
                    project_id=project_id,
                    requirement_id=req_res.id,
                    actor_id=current_user_id,
                    action="effort_confirmed",
                    message=f"Effort confirmed as {estimated_effort_days} days."
                )
            else:
                log_activity(
                    session=session,
                    project_id=project_id,
                    requirement_id=req_res.id,
                    actor_id=current_user_id,
                    action="effort_overridden",
                    message=f"Effort overridden from {suggested_effort_recommended_days} to {estimated_effort_days} days."
                )

        session.commit()
    except HTTPException:
        pass
    return RedirectResponse(url=f"/ui/projects/{project_id}", status_code=303)

@router.get("/requirements/{requirement_id}", response_class=HTMLResponse)
def requirement_details(requirement_id: int, request: Request, session: Session = Depends(get_session), current_user: User = Depends(require_current_user)):
    req = session.get(Requirement, requirement_id)
    if not req:
        raise HTTPException(status_code=404)
        
    project = session.get(ProjectGroup, req.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    assert project.id is not None
    users = session.exec(select(User)).all()
    
    change_requests = session.exec(
        select(ChangeRequest)
        .where(ChangeRequest.requirement_id == requirement_id)
    ).all()
    
    req_comments = session.exec(
        select(Comment, User)
        .join(User, col(Comment.user_id) == col(User.id))
        .where(Comment.requirement_id == requirement_id)
    ).all()
    
    activity_logs = session.exec(
        select(ActivityLog, User)
        .outerjoin(User, col(ActivityLog.actor_id) == col(User.id))
        .where(ActivityLog.requirement_id == requirement_id)
        .order_by(col(ActivityLog.created_at).asc())
    ).all()
    
    is_project_editable = project.status == ProjectStatus.active
    can_approve = can_approve_requirement(current_user, project.id, session)

    return templates.TemplateResponse(request=request, name="requirement_details.html", context={
        "request": request,
        "users": users,
        "current_user": current_user,
        "project": project,
        "requirement": req,
        "change_requests": change_requests,
        "comments": req_comments,
        "activity_logs": activity_logs,
        "is_project_editable": is_project_editable,
        "can_approve": can_approve
    })

@router.post("/projects/{project_id}/requirements/{requirement_id}/delete")
def delete_requirement(
    project_id: int,
    requirement_id: int,
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    project = session.get(ProjectGroup, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not can_manage_project(current_user, project_id, session):
        raise HTTPException(status_code=403, detail="Not authorized to delete requirements in this project")

    requirement = session.get(Requirement, requirement_id)
    if not requirement or requirement.project_id != project_id:
        raise HTTPException(status_code=404, detail="Requirement not found")

    # Check for linked records to prevent cascade delete of audit data
    linked_crs = session.exec(select(ChangeRequest).where(ChangeRequest.requirement_id == requirement_id)).first()
    linked_comments = session.exec(select(Comment).where(Comment.requirement_id == requirement_id)).first()
    
    has_review_history = requirement.status != RequirementStatus.submitted or requirement.reviewed_by_id is not None
    
    if linked_crs or linked_comments or has_review_history:
        url = f"/ui/projects/{project_id}?error=Cannot+delete+this+requirement+because+it+has+linked+change+requests,+comments,+or+review+history."
        return RedirectResponse(url=url, status_code=303)

    session.delete(requirement)
    session.commit()
    
    return RedirectResponse(url=f"/ui/projects/{project_id}?success=Requirement+deleted+successfully.", status_code=303)

@router.post("/projects/{project_id}/change-requests")
def create_change_request(
    project_id: int,
    title: str = Form(...),
    description: str = Form(""),
    reason: str = Form(""),
    impact: str = Form(""),
    requirement_id: Optional[int] = Form(None),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    project = session.get(ProjectGroup, project_id)
    if not project or project.status != ProjectStatus.active:
        raise HTTPException(status_code=403, detail="Project is not active")
        
    if not is_project_participant(current_user, project_id, session):
        raise HTTPException(status_code=403, detail="Not a participant in this project")
        
    current_user_id = current_user.id
    assert current_user_id is not None
    
    db_cr = ChangeRequest(
        project_id=project_id,
        requirement_id=requirement_id,
        title=title,
        description=description,
        reason=reason,
        impact=impact,
        requested_by=current_user_id
    )
    session.add(db_cr)
    
    log_activity(
        session=session,
        project_id=project_id,
        change_request_id=db_cr.id,
        actor_id=current_user_id,
        action="change_request_created",
        message=f"Created change request: {title}"
    )
    session.commit()
    
    return RedirectResponse(url=f"/ui/projects/{project_id}", status_code=303)

@router.post("/requirements/{requirement_id}/comments")
def add_requirement_comment(
    requirement_id: int,
    content: str = Form(...),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    req = session.get(Requirement, requirement_id)
    if not req or not is_project_participant(current_user, req.project_id, session):
        raise HTTPException(status_code=403, detail="Not a participant in this project")

    project = session.get(ProjectGroup, req.project_id)
    if not project or project.status != ProjectStatus.active:
        raise HTTPException(status_code=403, detail="Project is not active")
        
    assert project.id is not None
    current_user_id = current_user.id
    assert current_user_id is not None
    comment_create = CommentCreate(
        user_id=current_user_id,
        content=content
    )
    try:
        cr_api.add_requirement_comment(requirement_id, comment_create, session)
        log_activity(
            session=session,
            project_id=project.id,
            requirement_id=requirement_id,
            actor_id=current_user_id,
            action="comment_added",
            message="Added a comment."
        )
        session.commit()
    except HTTPException:
        pass
    return RedirectResponse(url=f"/ui/requirements/{requirement_id}", status_code=303)

@router.post("/change-requests/{change_request_id}/review")
def review_cr(
    change_request_id: int,
    action: str = Form(...),
    rejection_reason: str = Form(""),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    cr = session.get(ChangeRequest, change_request_id)
    if not cr:
        raise HTTPException(status_code=404)
        
    assert current_user.id is not None
        
    project = session.get(ProjectGroup, cr.project_id)
    if not project or project.status != ProjectStatus.active:
        raise HTTPException(status_code=403, detail="Project is not active")

    if not can_approve_change_request(current_user, cr.project_id, session):
        raise HTTPException(status_code=403, detail="Not authorized")
        
    if action not in [ChangeRequestStatus.approved.value, ChangeRequestStatus.rejected.value]:
        raise HTTPException(status_code=400, detail="Invalid action")
        
    if action == ChangeRequestStatus.rejected.value and not rejection_reason.strip():
        raise HTTPException(status_code=400, detail="Rejection reason mandatory")
        
    cr.status = ChangeRequestStatus(action)
    cr.reviewed_by_id = current_user.id
    cr.reviewed_at = datetime.now(timezone.utc)
    cr.updated_at = datetime.now(timezone.utc)
    if action == ChangeRequestStatus.approved.value:
        cr.rejection_reason = None
    else:
        cr.rejection_reason = rejection_reason.strip()
        
    session.add(cr)
    log_activity(
        session=session,
        project_id=cr.project_id,
        change_request_id=change_request_id,
        actor_id=current_user.id,
        action=f"change_request_{action}",
        message=f"Change request {action}"
    )
    session.commit()
    return RedirectResponse(url=f"/ui/projects/{cr.project_id}", status_code=303)

@router.get("/users", response_class=HTMLResponse)
def list_users_ui(request: Request, session: Session = Depends(get_session), current_user: User = Depends(require_current_user)):
    if not can_change_global_roles(current_user):
        raise HTTPException(status_code=403, detail="Only global admins can manage users")
        
    all_users = session.exec(select(User)).all()
    
    return templates.TemplateResponse(request=request, name="users.html", context={
        "request": request,
        "current_user": current_user,
        "users": all_users,
        "UserRole": UserRole
    })

@router.post("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    role: str = Form(...),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    if not can_change_global_roles(current_user):
        raise HTTPException(status_code=403, detail="Only global admins can change roles")
        
    target_user = session.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    new_role = UserRole(role)
    
    # Prevent removing the last admin
    if target_user.role == UserRole.admin and new_role != UserRole.admin:
        admin_count = session.exec(select(User).where(User.role == UserRole.admin)).all()
        if len(admin_count) <= 1:
            raise HTTPException(status_code=400, detail="Cannot remove the last global Admin")
            
    target_user.role = new_role
    session.add(target_user)
    session.commit()
    
    return RedirectResponse(url="/ui/users", status_code=303)

@router.post("/projects/{project_id}/status")
def update_project_status(
    project_id: int,
    status: str = Form(...),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    if not can_close_project(current_user):
        raise HTTPException(status_code=403, detail="Not authorized to change project status")
        
    project = session.get(ProjectGroup, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if status not in [ProjectStatus.active.value, ProjectStatus.completed.value, ProjectStatus.closed.value]:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    project.status = ProjectStatus(status)
    session.add(project)
    
    log_activity(
        session=session,
        project_id=project_id,
        actor_id=current_user.id,
        action=f"status_changed",
        message=f"Project status changed to {status}"
    )
    session.commit()
    
    return RedirectResponse(url=f"/ui/projects/{project_id}", status_code=303)

@router.post("/requirements/{requirement_id}/review")
def review_requirement(
    requirement_id: int,
    action: str = Form(...),
    rejection_reason: str = Form(""),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    req = session.get(Requirement, requirement_id)
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
        
    project = session.get(ProjectGroup, req.project_id)
    if not project or project.status != ProjectStatus.active:
        raise HTTPException(status_code=403, detail="Project is not active")
        
    if not can_approve_requirement(current_user, req.project_id, session):
        raise HTTPException(status_code=403, detail="Not authorized to review requirement")
        
    if action not in [RequirementStatus.approved.value, RequirementStatus.rejected.value, RequirementStatus.changes_requested.value]:
        raise HTTPException(status_code=400, detail="Invalid action")
        
    if action in [RequirementStatus.rejected.value, RequirementStatus.changes_requested.value] and not rejection_reason.strip():
        raise HTTPException(status_code=400, detail="Reason is mandatory for rejection or changes requested")
        
    req.status = RequirementStatus(action)
    req.reviewed_by_id = current_user.id
    req.reviewed_at = datetime.now(timezone.utc)
    req.updated_at = datetime.now(timezone.utc)
    
    if action == RequirementStatus.approved.value:
        req.rejection_reason = None
    else:
        req.rejection_reason = rejection_reason.strip()
        
    session.add(req)
    
    log_message = f"Changes requested: {req.rejection_reason}" if action == RequirementStatus.changes_requested.value else f"Requirement was {action}"
    
    log_activity(
        session=session,
        project_id=req.project_id,
        requirement_id=requirement_id,
        actor_id=current_user.id,
        action=f"requirement_{action}",
        message=log_message
    )
    session.commit()
    
    return RedirectResponse(url=f"/ui/projects/{req.project_id}", status_code=303)

@router.post("/requirements/{requirement_id}/metadata")
def update_requirement_metadata(
    requirement_id: int,
    complexity: Optional[str] = Form(None),
    business_value: Optional[str] = Form(None),
    estimated_effort_days: Optional[float] = Form(None),
    current_user: User = Depends(require_current_user),
    session: Session = Depends(get_session)
):
    req = session.get(Requirement, requirement_id)
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
        
    project = session.get(ProjectGroup, req.project_id)
    if not project or project.status != ProjectStatus.active:
        raise HTTPException(status_code=403, detail="Project is not active")
        
    if not can_approve_requirement(current_user, req.project_id, session):
        raise HTTPException(status_code=403, detail="Not authorized to update metadata")
        
    req.complexity = complexity if complexity else None
    req.business_value = business_value if business_value else None
    req.estimated_effort_days = estimated_effort_days if estimated_effort_days is not None else None
    req.updated_at = datetime.now(timezone.utc)
    
    session.add(req)
    
    log_activity(
        session=session,
        project_id=req.project_id,
        requirement_id=requirement_id,
        actor_id=current_user.id,
        action="metadata_updated",
        message=f"Requirement metadata updated"
    )
    session.commit()
    
    return RedirectResponse(url=f"/ui/requirements/{requirement_id}", status_code=303)
