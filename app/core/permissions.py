from sqlmodel import Session, select
from typing import Optional

from app.models.schema import User, UserRole, ProjectParticipant

def is_admin(user: User) -> bool:
    """Check if a user has the global Admin role."""
    return user.role == UserRole.admin

def get_project_participant(user_id: int, project_id: int, session: Session) -> Optional[ProjectParticipant]:
    """Get the participant record for a user in a specific project."""
    return session.exec(
        select(ProjectParticipant)
        .where(ProjectParticipant.project_id == project_id)
        .where(ProjectParticipant.user_id == user_id)
    ).first()

def is_project_participant(user: User, project_id: int, session: Session) -> bool:
    """Check if a user is a participant in a project (or a global admin)."""
    if is_admin(user):
        return True
    
    participant = get_project_participant(user.id, project_id, session)
    return participant is not None

def can_manage_project(user: User, project_id: int, session: Session) -> bool:
    """Check if a user has permissions to manage a project (add participants, edit project)."""
    if is_admin(user):
        return True
        
    participant = get_project_participant(user.id, project_id, session)
    if not participant:
        return False
        
    return participant.role in [UserRole.admin, UserRole.manager, UserRole.pm]

def can_create_project(user: User) -> bool:
    """Check if a user is allowed to create new projects globally."""
    return user.role in [UserRole.admin, UserRole.pm, UserRole.manager]

def can_change_global_roles(user: User) -> bool:
    """Check if a user is allowed to change global roles (Admin only)."""
    return is_admin(user)

def can_approve_requirement(user: User, project_id: int, session: Session) -> bool:
    """Check if a user is allowed to approve or reject a requirement."""
    if is_admin(user):
        return True
    
    participant = get_project_participant(user.id, project_id, session)
    if not participant:
        return False
        
    return participant.role in [UserRole.pm, UserRole.manager]

def can_close_project(user: User) -> bool:
    """Check if a user is allowed to close or reopen a project globally."""
    return is_admin(user)

def can_approve_change_request(user: User, project_id: int, session: Session) -> bool:
    """Check if a user is allowed to approve or reject a change request."""
    if is_admin(user):
        return True
    
    participant = get_project_participant(user.id, project_id, session)
    if not participant:
        return False
        
    return participant.role in [UserRole.pm, UserRole.manager]
