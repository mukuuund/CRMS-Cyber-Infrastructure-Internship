import httpx
import sys
import uuid

BASE_URL = "http://127.0.0.1:8000"

def print_result(status, step, details=""):
    if status == "PASS":
        print(f"PASS: {step}")
    elif status == "FAIL":
        print(f"FAIL: {step}")
        if details:
            print(f"   Details: {details}")
    elif status == "SKIP":
        print(f"SKIP: {step}")
        if details:
            print(f"   Reason: {details}")

def main():
    print(f"Starting API smoke tests against {BASE_URL}...\n")
    
    # Check if server is running
    try:
        r = httpx.get(f"{BASE_URL}/db-health", timeout=2.0)
        if r.status_code != 200:
            print(f"Error: Server health check failed (status: {r.status_code})")
            sys.exit(1)
    except httpx.RequestError as e:
        print(f"CRITICAL ERROR: Could not connect to FastAPI server at {BASE_URL}.")
        print("Please ensure the server is running (e.g., `uvicorn app.main:app --reload`) before executing the smoke test.")
        sys.exit(1)
        
    stats = {"pass": 0, "fail": 0, "skip": 0}
    unique_id = uuid.uuid4().hex[:6]
    
    # 1. Create User
    user_email = f"smoketest_{unique_id}@test.com"
    user_data = {
        "email": user_email,
        "password": "password123",
        "full_name": "Smoke Test User",
        "role": "admin"
    }
    
    try:
        r = httpx.post(f"{BASE_URL}/users/", json=user_data)
        if r.status_code == 201:
            user_id = r.json()["id"]
            print_result("PASS", "User created")
            stats["pass"] += 1
        else:
            print_result("FAIL", "User creation failed", f"POST /users/ | {r.status_code} | {r.text}")
            stats["fail"] += 1
            sys.exit(1)
    except Exception as e:
        print_result("FAIL", "User creation failed", f"Exception: {str(e)}")
        stats["fail"] += 1
        sys.exit(1)
        
    # 2. Create Project
    project_code = f"SMK-{unique_id}"
    project_data = {
        "project_code": project_code,
        "name": "Smoke Test Project",
        "description": "Project created by automated test.",
        "created_by": user_id
    }
    
    try:
        r = httpx.post(f"{BASE_URL}/projects/", json=project_data)
        if r.status_code == 201:
            project_id = r.json()["id"]
            print_result("PASS", "Project created")
            stats["pass"] += 1
        else:
            print_result("FAIL", "Project creation failed", f"POST /projects/ | {r.status_code} | {r.text}")
            stats["fail"] += 1
    except Exception as e:
        print_result("FAIL", "Project creation failed", f"Exception: {str(e)}")
        stats["fail"] += 1
        
    # 3. Add Participant
    # Create another user to add as participant
    part_user_data = {
        "email": f"smokepart_{unique_id}@test.com",
        "password": "pass",
        "full_name": "Participant",
        "role": "developer"
    }
    part_user_id = httpx.post(f"{BASE_URL}/users/", json=part_user_data).json()["id"]
    
    participant_data = {
        "user_id": part_user_id,
        "role": "developer"
    }
    try:
        r = httpx.post(f"{BASE_URL}/projects/{project_id}/participants", json=participant_data)
        if r.status_code == 200:
            print_result("PASS", "Participant added")
            stats["pass"] += 1
        else:
            print_result("FAIL", "Participant addition failed", f"POST /projects/{project_id}/participants | {r.status_code} | {r.text}")
            stats["fail"] += 1
    except Exception as e:
        print_result("FAIL", "Participant addition failed", f"Exception: {str(e)}")
        stats["fail"] += 1
        
    # 4. Create Requirement
    req_data = {
        "title": "Smoke Test Requirement",
        "description": "Test requirement description",
        "priority": "high",
        "created_by": user_id
    }
    try:
        r = httpx.post(f"{BASE_URL}/projects/{project_id}/requirements", json=req_data)
        if r.status_code == 201:
            req_id = r.json()["id"]
            print_result("PASS", "Requirement created")
            stats["pass"] += 1
        else:
            print_result("FAIL", "Requirement creation failed", f"POST /projects/{project_id}/requirements | {r.status_code} | {r.text}")
            stats["fail"] += 1
    except Exception as e:
        print_result("FAIL", "Requirement creation failed", f"Exception: {str(e)}")
        stats["fail"] += 1
        
    # 5. Create Change Request
    cr_data = {
        "title": "Smoke Test Change Request",
        "reason": "Because smoke testing.",
        "risk_level": "medium",
        "requested_by": user_id
    }
    try:
        r = httpx.post(f"{BASE_URL}/requirements/{req_id}/change-requests", json=cr_data)
        if r.status_code == 201:
            cr_id = r.json()["id"]
            print_result("PASS", "Change request submitted")
            stats["pass"] += 1
        else:
            print_result("FAIL", "Change request creation failed", f"POST /requirements/{req_id}/change-requests | {r.status_code} | {r.text}")
            stats["fail"] += 1
    except Exception as e:
        print_result("FAIL", "Change request creation failed", f"Exception: {str(e)}")
        stats["fail"] += 1
        
    # 6. Approve Change Request
    approval_data = {
        "decision": "approved",
        "remarks": "Approved by automated smoke test.",
        "approver_id": user_id
    }
    try:
        r = httpx.post(f"{BASE_URL}/change-requests/{cr_id}/approve", json=approval_data)
        if r.status_code == 200:
            print_result("PASS", "Change request approved")
            stats["pass"] += 1
        else:
            print_result("FAIL", "Change request approval failed", f"POST /change-requests/{cr_id}/approve | {r.status_code} | {r.text}")
            stats["fail"] += 1
    except Exception as e:
        print_result("FAIL", "Change request approval failed", f"Exception: {str(e)}")
        stats["fail"] += 1

    # 7. Add Comment to Requirement
    comment_data = {
        "content": "This is an automated comment on the requirement.",
        "user_id": user_id
    }
    try:
        r = httpx.post(f"{BASE_URL}/requirements/{req_id}/comments", json=comment_data)
        if r.status_code == 200:
            print_result("PASS", "Comment added to requirement")
            stats["pass"] += 1
        else:
            print_result("FAIL", "Comment addition to requirement failed", f"POST /requirements/{req_id}/comments | {r.status_code} | {r.text}")
            stats["fail"] += 1
    except Exception as e:
        print_result("FAIL", "Comment addition to requirement failed", f"Exception: {str(e)}")
        stats["fail"] += 1

    # 8. Verify data exists (Fetch projects)
    try:
        r = httpx.get(f"{BASE_URL}/projects/{project_id}")
        if r.status_code == 200 and r.json()["project_code"] == project_code:
            print_result("PASS", "Final data verified (Project fetch successful)")
            stats["pass"] += 1
        else:
            print_result("FAIL", "Final data verification failed", f"GET /projects/{project_id} | {r.status_code} | {r.text}")
            stats["fail"] += 1
    except Exception as e:
        print_result("FAIL", "Final data verification failed", f"Exception: {str(e)}")
        stats["fail"] += 1

    print("\n--- Smoke Test Summary ---")
    print(f"Total checks passed: {stats['pass']}")
    print(f"Total checks failed: {stats['fail']}")
    print(f"Total checks skipped: {stats['skip']}")
    
    if stats["fail"] > 0:
        print("\nOVERALL RESULT: FAIL")
        sys.exit(1)
    else:
        print("\nOVERALL RESULT: PASS")

if __name__ == "__main__":
    main()
