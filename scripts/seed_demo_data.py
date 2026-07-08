# pyright: reportCallIssue=false
import sys
import os
from datetime import datetime, timezone, timedelta

# Add parent directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from app.core.database import engine
from app.models.schema import (
    User, UserRole, ProjectGroup, ProjectStatus, ProjectParticipant, ParticipantStatus,
    Requirement, RequirementPriority, RequirementStatus, ChangeRequest, ChangeRequestRiskLevel,
    ChangeRequestStatus, ChangeApproval, ApprovalDecision, Comment, ActivityLog
)
from app.core.security import get_password_hash

def seed_data():
    print("Starting demo data seeding...")
    
    with Session(engine) as session:
        # --- 1. Seed Users ---
        users_data = [
            {"email": "admin@demo.com", "password": "password123", "full_name": "Admin User", "role": UserRole.admin},
            {"email": "pm@demo.com", "password": "password123", "full_name": "Project Manager", "role": UserRole.pm},
            {"email": "ba@demo.com", "password": "password123", "full_name": "Business Analyst", "role": UserRole.ba},
            {"email": "dev@demo.com", "password": "password123", "full_name": "Lead Developer", "role": UserRole.developer},
            {"email": "client@demo.com", "password": "password123", "full_name": "Client Representative", "role": UserRole.client},
            {"email": "manager@demo.com", "password": "password123", "full_name": "Operations Manager", "role": UserRole.manager},
        ]
        
        db_users = {}
        users_created = 0
        users_found = 0
        
        for u_data in users_data:
            user = session.exec(select(User).where(User.email == u_data["email"])).first()
            if not user:
                user = User(
                    email=u_data["email"],
                    hashed_password=get_password_hash(u_data["password"]),
                    full_name=u_data["full_name"],
                    role=u_data["role"]
                )  # type: ignore
                session.add(user)
                session.commit()
                session.refresh(user)
                users_created += 1
            else:
                users_found += 1
            db_users[u_data["role"]] = user
        
        print(f"Users: {users_created} created, {users_found} found (total {len(db_users)})")
        
        # --- 2. Seed Projects ---
        projects_data = [
            {"project_code": "PRJ-Alpha", "name": "Project Alpha Redesign", "description": "Complete UI/UX redesign of the Alpha platform.", "created_by": db_users[UserRole.pm].id},
            {"project_code": "PRJ-Beta", "name": "Beta API Integration", "description": "Integration with the new Beta payment gateway.", "created_by": db_users[UserRole.pm].id},
        ]
        
        db_projects = []
        projects_created = 0
        projects_found = 0
        
        for p_data in projects_data:
            project = session.exec(select(ProjectGroup).where(ProjectGroup.project_code == p_data["project_code"])).first()
            if not project:
                project = ProjectGroup(
                    project_code=p_data["project_code"],
                    name=p_data["name"],
                    description=p_data["description"],
                    created_by=p_data["created_by"]
                )  # type: ignore
                session.add(project)
                session.commit()
                session.refresh(project)
                projects_created += 1
            else:
                projects_found += 1
            db_projects.append(project)
        
        print(f"Projects: {projects_created} created, {projects_found} found")
        
        # --- 3. Seed Participants ---
        participants_created = 0
        participants_found = 0
        
        for project in db_projects:
            # Add all demo users to the project if not already present
            for role, user in db_users.items():
                participant = session.exec(
                    select(ProjectParticipant)
                    .where(ProjectParticipant.project_id == project.id)
                    .where(ProjectParticipant.user_id == user.id)
                ).first()
                if not participant:
                    participant = ProjectParticipant(
                        project_id=project.id,
                        user_id=user.id,
                        role=user.role
                    )  # type: ignore
                    session.add(participant)
                    session.commit()
                    participants_created += 1
                else:
                    participants_found += 1
                    
        print(f"Participants: {participants_created} created, {participants_found} found")
        
        # --- 4. Seed Requirements (8 Realistic Reqs) ---
        reqs_data = [
            {
                "title": "OAuth2 Login Integration", "description": "Implement OAuth2 login using Google and Microsoft providers.", 
                "project_idx": 0, "priority": RequirementPriority.high, "status": RequirementStatus.approved,
                "created_by": db_users[UserRole.ba].id, "owner_id": db_users[UserRole.developer].id,
                "complexity": "medium", "business_value": "high", "estimated_effort_days": 5.0,
                "ai_suggested_priority": "high", "ai_confidence": 0.88, "ai_low_probability": 0.05, "ai_medium_probability": 0.07, "ai_high_probability": 0.88, "priority_overridden": False,
                "rejection_reason": None, "comments": ["Great requirement, properly detailed."]
            },
            {
                "title": "Export Reports to PDF", "description": "Users need to export their analytics dashboard to PDF format.", 
                "project_idx": 0, "priority": RequirementPriority.low, "status": RequirementStatus.changes_requested,
                "created_by": db_users[UserRole.client].id, "owner_id": None,
                "complexity": "low", "business_value": "low", "estimated_effort_days": 2.0,
                "ai_suggested_priority": "low", "ai_confidence": 0.92, "ai_low_probability": 0.92, "ai_medium_probability": 0.06, "ai_high_probability": 0.02, "priority_overridden": False,
                "rejection_reason": "Please specify which charts need to be included in the PDF.", "comments": ["The client forgot to specify the charts."]
            },
            {
                "title": "Dashboard Performance Optimization", "description": "Reduce load time of the main dashboard to under 1 second.", 
                "project_idx": 0, "priority": RequirementPriority.high, "status": RequirementStatus.submitted,
                "created_by": db_users[UserRole.developer].id, "owner_id": db_users[UserRole.developer].id,
                "complexity": "high", "business_value": "medium", "estimated_effort_days": 8.5,
                "ai_suggested_priority": "medium", "ai_confidence": 0.65, "ai_low_probability": 0.15, "ai_medium_probability": 0.65, "ai_high_probability": 0.20, "priority_overridden": True,
                "rejection_reason": None, "comments": []
            },
            {
                "title": "User Profile Avatar Upload", "description": "Allow users to upload custom profile pictures.", 
                "project_idx": 0, "priority": RequirementPriority.low, "status": RequirementStatus.rejected,
                "created_by": db_users[UserRole.client].id, "owner_id": None,
                "complexity": "low", "business_value": "low", "estimated_effort_days": 3.0,
                "ai_suggested_priority": "low", "ai_confidence": 0.78, "ai_low_probability": 0.78, "ai_medium_probability": 0.20, "ai_high_probability": 0.02, "priority_overridden": False,
                "rejection_reason": "Not in scope for this quarter.", "comments": []
            },
            {
                "title": "Stripe Payment Gateway Integration", "description": "Process customer subscriptions via Stripe API.", 
                "project_idx": 1, "priority": RequirementPriority.high, "status": RequirementStatus.approved,
                "created_by": db_users[UserRole.pm].id, "owner_id": db_users[UserRole.developer].id,
                "complexity": "high", "business_value": "high", "estimated_effort_days": 12.0,
                "ai_suggested_priority": "high", "ai_confidence": 0.95, "ai_low_probability": 0.01, "ai_medium_probability": 0.04, "ai_high_probability": 0.95, "priority_overridden": False,
                "rejection_reason": None, "comments": ["Critical for revenue. Let's start this sprint."]
            },
            {
                "title": "Email Notification Service", "description": "Send welcome emails and password reset emails.", 
                "project_idx": 1, "priority": RequirementPriority.medium, "status": RequirementStatus.submitted,
                "created_by": db_users[UserRole.ba].id, "owner_id": None,
                "complexity": "medium", "business_value": "medium", "estimated_effort_days": 4.0,
                "ai_suggested_priority": "medium", "ai_confidence": 0.81, "ai_low_probability": 0.10, "ai_medium_probability": 0.81, "ai_high_probability": 0.09, "priority_overridden": False,
                "rejection_reason": None, "comments": []
            },
            {
                "title": "Data Anonymization Script", "description": "Scrub PII data for staging environments.", 
                "project_idx": 1, "priority": RequirementPriority.medium, "status": RequirementStatus.changes_requested,
                "created_by": db_users[UserRole.developer].id, "owner_id": db_users[UserRole.developer].id,
                "complexity": "high", "business_value": "low", "estimated_effort_days": 7.0,
                "ai_suggested_priority": "high", "ai_confidence": 0.55, "ai_low_probability": 0.05, "ai_medium_probability": 0.40, "ai_high_probability": 0.55, "priority_overridden": True,
                "rejection_reason": "Need to clarify exactly which tables are considered PII.", "comments": ["Security team needs to review the table list."]
            },
            {
                "title": "Dark Mode Support", "description": "Implement a dark mode toggle for the UI.", 
                "project_idx": 1, "priority": RequirementPriority.low, "status": RequirementStatus.submitted,
                "created_by": db_users[UserRole.client].id, "owner_id": None,
                "complexity": "medium", "business_value": "low", "estimated_effort_days": 6.0,
                "ai_suggested_priority": "low", "ai_confidence": 0.89, "ai_low_probability": 0.89, "ai_medium_probability": 0.10, "ai_high_probability": 0.01, "priority_overridden": False,
                "rejection_reason": None, "comments": []
            }
        ]
        
        db_reqs = []
        reqs_created = 0
        reqs_found = 0
        
        for r_data in reqs_data:
            project_id = db_projects[r_data["project_idx"]].id
            req = session.exec(
                select(Requirement)
                .where(Requirement.project_id == project_id)
                .where(Requirement.title == r_data["title"])
            ).first()
            if not req:
                req = Requirement(
                    project_id=project_id,
                    title=r_data["title"],
                    description=r_data["description"],
                    priority=r_data["priority"],
                    status=r_data["status"],
                    created_by=r_data["created_by"],
                    owner_id=r_data["owner_id"],
                    complexity=r_data["complexity"],
                    business_value=r_data["business_value"],
                    estimated_effort_days=r_data["estimated_effort_days"],
                    ai_suggested_priority=r_data["ai_suggested_priority"],
                    ai_confidence=r_data["ai_confidence"],
                    ai_low_probability=r_data["ai_low_probability"],
                    ai_medium_probability=r_data["ai_medium_probability"],
                    ai_high_probability=r_data["ai_high_probability"],
                    priority_overridden=r_data["priority_overridden"],
                    rejection_reason=r_data["rejection_reason"]
                )  # type: ignore
                
                if r_data["status"] in [RequirementStatus.approved, RequirementStatus.rejected, RequirementStatus.changes_requested]:
                    req.reviewed_by_id = db_users[UserRole.manager].id
                    req.reviewed_at = datetime.now(timezone.utc)
                    
                session.add(req)
                session.commit()
                session.refresh(req)
                
                # Create corresponding Activity Logs
                logs = [
                    ActivityLog(project_id=project_id, requirement_id=req.id, actor_id=req.created_by, action="requirement_created", message=f"Created requirement: {req.title}"),
                    ActivityLog(project_id=project_id, requirement_id=req.id, actor_id=None, action="ai_priority_suggested", message=f"AI suggested {req.ai_suggested_priority.upper()} priority with {int(req.ai_confidence*100)}% confidence."),
                    ActivityLog(project_id=project_id, requirement_id=req.id, actor_id=req.created_by, action="priority_overridden" if req.priority_overridden else "priority_confirmed", message=f"Priority {'overridden to' if req.priority_overridden else 'confirmed as'} {req.priority.value}")
                ]
                
                if req.status == RequirementStatus.approved:
                    logs.append(ActivityLog(project_id=project_id, requirement_id=req.id, actor_id=req.reviewed_by_id, action="requirement_approved", message="Requirement was approved"))
                elif req.status == RequirementStatus.rejected:
                    logs.append(ActivityLog(project_id=project_id, requirement_id=req.id, actor_id=req.reviewed_by_id, action="requirement_rejected", message="Requirement was rejected"))
                elif req.status == RequirementStatus.changes_requested:
                    logs.append(ActivityLog(project_id=project_id, requirement_id=req.id, actor_id=req.reviewed_by_id, action="requirement_changes_requested", message=f"Changes requested: {req.rejection_reason}"))
                
                for log in logs:
                    session.add(log)
                    
                for c_text in r_data["comments"]:
                    comment = Comment(user_id=db_users[UserRole.pm].id, requirement_id=req.id, content=c_text) # type: ignore
                    session.add(comment)
                    session.add(ActivityLog(project_id=project_id, requirement_id=req.id, actor_id=db_users[UserRole.pm].id, action="comment_added", message="Added a comment."))
                    
                session.commit()
                reqs_created += 1
            else:
                reqs_found += 1
            db_reqs.append(req)
            
        print(f"Requirements: {reqs_created} created, {reqs_found} found")
        
        print("\nDemo data seeding completed successfully!")

if __name__ == "__main__":
    seed_data()
