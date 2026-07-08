from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from app.models.schema import (
    UserRole, ProjectStatus, RequirementPriority, RequirementStatus, 
    ChangeRequestRiskLevel, ChangeRequestStatus, ApprovalDecision
)

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: Optional[UserRole] = UserRole.client

class UserRead(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    created_at: datetime

class ProjectCreate(BaseModel):
    project_code: str
    name: str
    description: Optional[str] = None
    created_by: int

class ProjectRead(BaseModel):
    id: int
    project_code: str
    name: str
    description: Optional[str]
    status: ProjectStatus
    created_by: int
    created_at: datetime

class ParticipantAdd(BaseModel):
    user_id: int
    role: UserRole

class RequirementCreate(BaseModel):
    title: str
    description: Optional[str] = None
    module: Optional[str] = None
    priority: RequirementPriority
    acceptance_criteria: Optional[str] = None
    due_date: Optional[date] = None
    created_by: int
    owner_id: Optional[int] = None
    complexity: Optional[str] = None
    business_value: Optional[str] = None
    estimated_effort_days: Optional[float] = None
    ai_suggested_priority: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_low_probability: Optional[float] = None
    ai_medium_probability: Optional[float] = None
    ai_high_probability: Optional[float] = None
    suggested_effort_min_days: Optional[float] = None
    suggested_effort_max_days: Optional[float] = None
    suggested_effort_recommended_days: Optional[float] = None
    suggested_effort_reason: Optional[str] = None
    effort_overridden: bool = False

class ChangeRequestCreate(BaseModel):
    title: str
    description: Optional[str] = None
    reason: Optional[str] = None
    impact: Optional[str] = None
    requirement_id: Optional[int] = None
    requested_by: int

class ApprovalDecisionCreate(BaseModel):
    decision: ApprovalDecision
    remarks: Optional[str] = None
    approver_id: int

class CommentCreate(BaseModel):
    content: str
    user_id: int
