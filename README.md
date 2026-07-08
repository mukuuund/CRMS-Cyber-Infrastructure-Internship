# CRMS

Client Requirement & Change Request Management System

## Project Overview

CRMS (Client Requirement & Change Request Management System) is a working prototype web application designed for software service companies. It provides a centralized platform to manage evolving client requirements, handle change requests, and facilitate collaboration among project participants throughout the software development lifecycle.

## Problem Statement

In software service projects, client requirements frequently evolve after the initial scoping phase. Managing these changes through unstructured channels like emails or spreadsheets leads to miscommunication, scope creep, and unclear approval trails. A dedicated system is needed to formalize the change request process, ensure proper stakeholder approvals, and maintain a clear history of requirement modifications.

## Purpose of the Prototype

This project serves as a working prototype built for the Cyber Infrastructure Internship. It demonstrates a structured approach to requirement management, complete with role-based access control, integrated approval workflows, and automated priority suggestions to streamline project delivery.

## Key Features

- **User Authentication:** Secure login and signup functionality for all users.
- **Role-Based Access Control:** Distinct permissions and views for Admin, PM (Project Manager), Manager, BA (Business Analyst), Developer, and Client roles.
- **Project Creation and Management:** Centralized dashboard to view and manage multiple projects.
- **Project Participants:** Invite and assign users to specific projects with designated roles.
- **Requirement Management:** Create, view, and update detailed project requirements.
- **Change Request Workflow:** Submit modifications to existing requirements through a formalized change request process.
- **Approval/Rejection Flow:** PMs and Clients can approve, reject, or request further changes on submitted requirements and change requests.
- **Comments and Collaboration:** Threaded discussions on requirements for seamless team communication.
- **Dashboard:** High-level overview of active projects and recent activities.
- **ML-Based Priority Suggestion:** Automated, AI-driven priority estimations for incoming requirements based on natural language processing.

## User Roles

- **Admin:** Full system access, including user and role management.
- **Project Manager (PM) / Manager:** Oversees project progress, assigns resources, and approves requirements/change requests.
- **Business Analyst (BA):** Gathers and documents requirements, and communicates with clients.
- **Developer:** Reviews technical feasibility and implements approved requirements.
- **Client:** Submits requirements, requests changes, and provides final approvals on proposed scopes.

## How the System Works

The system operates as a unified web portal where authenticated users interact based on their assigned roles. When a project is created, participants are invited. Clients or BAs can log requirements into the system. The built-in ML model analyzes the text to suggest an initial priority. As the project progresses, any modifications to the agreed scope must go through the Change Request workflow, which requires explicit approval from authorized roles (like the PM or Client) before implementation begins.

## Basic Workflow

1. **Authentication:** Users register and log into the system.
2. **Project Setup:** An Admin or Manager creates a project and adds participants.
3. **Requirement Gathering:** BAs or Clients submit new project requirements. The ML model suggests a priority level.
4. **Review & Approval:** The PM reviews the requirement, adjusts metadata (like effort estimations), and approves it.
5. **Change Management:** If a requirement needs modification later, a Change Request is raised.
6. **Collaboration:** Team members discuss the change via the comments section.
7. **Final Decision:** The PM or Client formally approves or rejects the change request, updating the project scope.

## Technology Stack

- **Backend:** Python, FastAPI
- **Database ORM:** SQLModel / SQLAlchemy
- **Migrations:** Alembic
- **Frontend:** HTML, CSS, JavaScript, Jinja2 Templates
- **Databases:** SQLite (ready for local development), PostgreSQL-ready structure for deployment
- **Machine Learning:** PyTorch / Scikit-learn (for ML-based priority prediction)

## Project Structure

```text
├── alembic/                # Database migration scripts
├── app/
│   ├── api/                # API routers for users, projects, requirements, etc.
│   ├── core/               # Database, security, and app configuration
│   ├── ml/                 # ML predictor and model architecture
│   ├── models/             # Database schemas (SQLModel)
│   ├── static/             # CSS and JavaScript assets
│   ├── templates/          # Jinja2 HTML templates
│   ├── auth_routes.py      # Authentication frontend routes
│   ├── frontend_routes.py  # UI rendering routes
│   └── main.py             # FastAPI application entry point
├── models/
│   └── priority_model/     # Trained ML model weights and configuration
├── scripts/                # Utility scripts for database reset and testing
├── .env                    # Environment variables
├── alembic.ini             # Alembic configuration
├── requirements.txt        # Python dependencies
└── run.py                  # Startup script with auto-browser launch
```

## Installation and Setup

Follow these steps to set up the prototype on your local machine:

```bash
# 1. Clone the repository
git clone <repository-url>
cd <project-folder>

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate the virtual environment
# For Windows:
.venv\Scripts\activate
# For macOS/Linux:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure environment variables
# Ensure your .env file is set up with your DATABASE_URL
# Example for PostgreSQL: DATABASE_URL=postgresql://user:password@localhost:5432/db_name

# 6. Run database migrations
alembic upgrade head
```

## Running the Application

To start the FastAPI server and automatically open the application in your default web browser, run:

```bash
python run.py
```

Alternatively, you can start the Uvicorn server directly:

```bash
uvicorn app.main:app --reload
```

## Database Migration

If you make any changes to the database models in `app/models/schema.py`, generate and apply a new migration using Alembic:

```bash
# Generate a new migration script
alembic revision --autogenerate -m "Description of changes"

# Apply the migration to the database
alembic upgrade head
```

## Use Case

This prototype is best suited for IT consultancies, freelance agencies, or internal software departments that suffer from disorganized requirement tracking. By enforcing a strict change request protocol, CRMS ensures that developers only work on approved features and that clients are always aware of scope changes.

## Future Enhancements

- Email notifications for pending approvals and mentions.
- Detailed reporting and analytics dashboards for project velocity.
- Integration with external issue trackers like Jira or GitHub Issues.
- Enhanced ML models for automated effort estimation.

## Project Status

**Working Prototype:** The core functionality (authentication, CRUD operations for projects/requirements, change workflows, and ML inference) is fully implemented and operational. It is currently being used for demonstration and internship evaluation purposes.
