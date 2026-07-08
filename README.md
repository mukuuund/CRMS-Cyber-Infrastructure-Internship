# Change Requirement Management System (CRMS)

## Project Overview
This is a FastAPI-based robust web application designed for managing software projects, their requirements, and change requests. It features a complete role-based human-in-the-loop workflow tailored for enterprise teams (Project Managers, Business Analysts, Developers, Clients, etc.).

## Tech Stack
- **Backend**: FastAPI (Python 3)
- **Database ORM**: SQLModel (SQLAlchemy under the hood)
- **Database**: PostgreSQL (Migrations tracked with Alembic)
- **Frontend**: Jinja2 Templates (HTML/CSS)
- **Machine Learning**: Custom internal LightGBM/Scikit-learn model for priority suggestions.

## Core Features
1. **Role-Based Access Control**: Admins, PMs, BAs, Developers, and Clients.
2. **Project & Requirement Tracking**: Comprehensive metadata (complexity, business value, estimated effort) and priority tracking.
3. **Change Requests**: Formalized process for submitting and approving change requests.
4. **Activity Logs**: Immutable, chronological audit trails of all critical actions on a requirement.
5. **Collaboration**: Comment threads directly on requirements and change requests.

## AI Priority Suggestion Feature
The platform integrates an intelligent "V3 AI Priority Suggestion" model as its **only** active machine learning feature. When creating a requirement, a user can click "Suggest AI Priority". The system provides a real-time recommendation (LOW, MEDIUM, or HIGH) along with confidence probabilities.

**Known Limitation & Design Choice:** 
The AI V3 model acts purely as an **assistant**. It does not perform automatic production decisioning. The human user must review the AI suggestion, and they can explicitly confirm it or override it before saving the requirement. The system formally audits whether the AI was overridden via the Activity Log.

## Rule-Based Effort Estimation
We previously explored ML models for predicting requirement completion time, but these experiments were rejected. The dataset measured noisy calendar resolution time, which was not an accurate proxy for true developer effort. Instead, effort estimation is now completely deterministic and **rule-based**, calculating a suggested range based on Priority, Complexity, and Business Value.

## Setup & Running the Application

### 1. Database Migrations
Ensure your database is up to date:
```bash
alembic upgrade head
```

### 2. Reset and Seed Demo Data
To start completely fresh with realistic demo data, you can run the reset script. **Warning: This drops all tables.**
```bash
python scripts/reset_db.py
```
*(This automatically runs `alembic upgrade head` and `scripts/seed_demo_data.py`.)*

### 3. Running the Server
Start the application on `localhost:8000`:
```bash
python run.py
# or
uvicorn app.main:app --reload
```

## Demo Flow
A comprehensive step-by-step walkthrough is available at `docs/demo_flow.md`.
Please review this file to understand the intended journey for demonstrating the platform.
