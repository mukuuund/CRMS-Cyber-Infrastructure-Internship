from sqlmodel import Session
from typing import Optional
from app.models.schema import ActivityLog

def log_activity(
    session: Session, 
    project_id: int, 
    requirement_id: Optional[int] = None, 
    change_request_id: Optional[int] = None, 
    actor_id: Optional[int] = None, 
    action: str = "", 
    message: str = ""
):
    """
    Safely logs an activity. Does not commit the session itself, just adds to it.
    If logging fails, we log it and continue.
    """
    try:
        activity = ActivityLog(
            project_id=project_id,
            requirement_id=requirement_id,
            change_request_id=change_request_id,
            actor_id=actor_id,
            action=action,
            message=message
        )
        session.add(activity)
    except Exception as e:
        print(f"Failed to log activity {action}: {e}")
