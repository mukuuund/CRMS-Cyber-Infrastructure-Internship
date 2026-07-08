import sys
import os

# Add parent directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from app.core.database import engine
from app.models.schema import User, ProjectGroup, Requirement, ActivityLog, RequirementStatus

def smoke_test():
    print("Running Smoke Test on Demo Data...\n")
    
    with Session(engine) as session:
        # 1. Users
        users = session.exec(select(User)).all()
        assert len(users) >= 6, f"Expected at least 6 users, found {len(users)}"
        print(f"PASS: Found {len(users)} users.")
        
        # 2. Projects
        projects = session.exec(select(ProjectGroup)).all()
        assert len(projects) >= 2, f"Expected at least 2 projects, found {len(projects)}"
        print(f"PASS: Found {len(projects)} projects.")
        
        # 3. Requirements
        reqs = session.exec(select(Requirement)).all()
        assert len(reqs) == 8, f"Expected exactly 8 requirements, found {len(reqs)}"
        print(f"PASS: Found {len(reqs)} requirements.")
        
        # 4. Statuses
        statuses = {r.status for r in reqs}
        expected_statuses = {RequirementStatus.submitted, RequirementStatus.approved, RequirementStatus.rejected, RequirementStatus.changes_requested}
        assert statuses == expected_statuses, f"Expected statuses {expected_statuses}, found {statuses}"
        print(f"PASS: All expected statuses are present: {[s.value for s in statuses]}")
        
        # 5. AI Fields
        ai_populated = sum(1 for r in reqs if r.ai_suggested_priority is not None)
        assert ai_populated == 8, f"Expected 8 requirements with AI priority, found {ai_populated}"
        print(f"PASS: All requirements have AI priority fields populated.")
        
        # 6. Activity Logs
        logs = session.exec(select(ActivityLog)).all()
        assert len(logs) > 10, f"Expected multiple activity logs, found {len(logs)}"
        print(f"PASS: Found {len(logs)} activity logs.")
        
        print("\nSmoke test passed! Database is ready for demo.")

if __name__ == "__main__":
    try:
        smoke_test()
    except AssertionError as e:
        print(f"FAIL: Smoke test failed: {e}")
        sys.exit(1)
