import enum
from typing import Optional
from datetime import datetime, date, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String, BigInteger, ForeignKey, CheckConstraint, UniqueConstraint, Float

# --- Enums ---
class UserRole(str, enum.Enum):
    admin = "admin"
    pm = "pm"
    ba = "ba"
    developer = "developer"
    client = "client"
    manager = "manager"

class ProjectStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    closed = "closed"

class InviteStatus(str, enum.Enum):
    invite_sent = "invite_sent"
    accepted = "accepted"
    declined = "declined"
    expired = "expired"

class ParticipantStatus(str, enum.Enum):
    active = "active"
    removed = "removed"

class RequirementPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class RequirementStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    approved = "approved"
    rejected = "rejected"
    changes_requested = "changes_requested"
    in_progress = "in_progress"
    completed = "completed"

class ChangeRequestStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    approved = "approved"
    rejected = "rejected"
    completed = "completed"

class ChangeRequestRiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"

class ApprovalDecision(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    needs_clarification = "needs_clarification"

# --- Models ---
class User(SQLModel, table=True):
    __tablename__: str = "users" # type: ignore
    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    email: str = Field(sa_column=Column(String, unique=True, index=True, nullable=False))
    hashed_password: str = Field(nullable=False)
    full_name: str = Field(nullable=False)
    role: UserRole
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProjectGroup(SQLModel, table=True):
    __tablename__: str = "project_groups" # type: ignore
    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    project_code: str = Field(sa_column=Column(String, unique=True, index=True, nullable=False))
    name: str = Field(nullable=False)
    description: Optional[str] = None
    status: ProjectStatus = Field(default=ProjectStatus.active)
    created_by: int = Field(sa_column=Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProjectInvite(SQLModel, table=True):
    __tablename__: str = "project_invites" # type: ignore
    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    project_id: int = Field(sa_column=Column(BigInteger, ForeignKey("project_groups.id", ondelete="CASCADE"), nullable=False, index=True))
    email: str = Field(nullable=False)
    role: UserRole
    invite_token: str = Field(sa_column=Column(String, unique=True, index=True, nullable=False))
    invited_by: int = Field(sa_column=Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False))
    status: InviteStatus = Field(default=InviteStatus.invite_sent)
    expires_at: datetime = Field(nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProjectParticipant(SQLModel, table=True):
    __tablename__: str = "project_participants" # type: ignore
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_user"),)
    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    project_id: int = Field(sa_column=Column(BigInteger, ForeignKey("project_groups.id", ondelete="CASCADE"), nullable=False, index=True))
    user_id: int = Field(sa_column=Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True))
    role: UserRole
    status: ParticipantStatus = Field(default=ParticipantStatus.active)
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Requirement(SQLModel, table=True):
    __tablename__: str = "requirements" # type: ignore
    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    project_id: int = Field(sa_column=Column(BigInteger, ForeignKey("project_groups.id", ondelete="CASCADE"), nullable=False, index=True))
    title: str = Field(nullable=False)
    description: Optional[str] = None
    module: Optional[str] = None
    priority: RequirementPriority
    status: RequirementStatus = Field(default=RequirementStatus.submitted)
    acceptance_criteria: Optional[str] = None
    owner_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL")))
    created_by: int = Field(sa_column=Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False))
    due_date: Optional[date] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reviewed_by_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL")))
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    updated_at: Optional[datetime] = None
    
    # ML-ready fields
    complexity: Optional[str] = Field(default=None, sa_column=Column(String))
    business_value: Optional[str] = Field(default=None, sa_column=Column(String))
    estimated_effort_days: Optional[float] = Field(default=None, sa_column=Column(Float))
    
    # AI Priority tracking fields
    ai_suggested_priority: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_low_probability: Optional[float] = Field(default=None, sa_column=Column(Float))
    ai_medium_probability: Optional[float] = Field(default=None, sa_column=Column(Float))
    ai_high_probability: Optional[float] = Field(default=None, sa_column=Column(Float))
    priority_overridden: bool = Field(default=False)
    
    # Rule-based Effort tracking
    suggested_effort_min_days: Optional[float] = Field(default=None, sa_column=Column(Float))
    suggested_effort_max_days: Optional[float] = Field(default=None, sa_column=Column(Float))
    suggested_effort_recommended_days: Optional[float] = Field(default=None, sa_column=Column(Float))
    suggested_effort_reason: Optional[str] = Field(default=None, sa_column=Column(String))
    effort_overridden: bool = Field(default=False)

class ChangeRequest(SQLModel, table=True):
    __tablename__: str = "change_requests" # type: ignore
    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    project_id: int = Field(sa_column=Column(BigInteger, ForeignKey("project_groups.id", ondelete="CASCADE"), nullable=False, index=True))
    requirement_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, ForeignKey("requirements.id", ondelete="CASCADE"), index=True))
    title: str = Field(nullable=False)
    description: Optional[str] = None
    reason: Optional[str] = None
    impact: Optional[str] = None
    status: ChangeRequestStatus = Field(default=ChangeRequestStatus.submitted)
    requested_by: int = Field(sa_column=Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False))
    reviewed_by_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL")))
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

class ActivityLog(SQLModel, table=True):
    __tablename__: str = "activity_logs" # type: ignore
    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    project_id: int = Field(sa_column=Column(BigInteger, ForeignKey("project_groups.id", ondelete="CASCADE"), nullable=False, index=True))
    requirement_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, ForeignKey("requirements.id", ondelete="CASCADE"), index=True))
    change_request_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, ForeignKey("change_requests.id", ondelete="CASCADE"), index=True))
    actor_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), index=True))
    action: str = Field(nullable=False, index=True)
    message: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChangeApproval(SQLModel, table=True):
    __tablename__: str = "change_approvals" # type: ignore
    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    change_request_id: int = Field(sa_column=Column(BigInteger, ForeignKey("change_requests.id", ondelete="CASCADE"), nullable=False, index=True))
    approver_id: int = Field(sa_column=Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False))
    decision: ApprovalDecision = Field(default=ApprovalDecision.pending)
    remarks: Optional[str] = None
    decided_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Comment(SQLModel, table=True):
    __tablename__: str = "comments" # type: ignore
    __table_args__ = (
        CheckConstraint(
            "(requirement_id IS NOT NULL AND change_request_id IS NULL) OR "
            "(requirement_id IS NULL AND change_request_id IS NOT NULL)",
            name="chk_comment_target"
        ),
    )
    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    user_id: int = Field(sa_column=Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True))
    requirement_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, ForeignKey("requirements.id", ondelete="CASCADE"), index=True))
    change_request_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, ForeignKey("change_requests.id", ondelete="CASCADE"), index=True))
    content: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
