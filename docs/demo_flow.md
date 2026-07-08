# CRMS Demo Flow Walkthrough

This document outlines the ideal demo flow to showcase the capabilities of the CRMS (Change Requirement Management System), including the AI priority suggestion, metadata tracking, and the review loop.

## Setup
Before starting the demo, ensure you have reset the database and seeded the demo data:
```bash
python scripts/reset_db.py
```
Start the application:
```bash
uvicorn app.main:app --reload
```

## Step-by-step Demo

### 1. Login & Dashboard
- Navigate to `http://127.0.0.1:8000/ui/login`.
- Login as the Project Manager (`pm@demo.com` / `password123`).
- **Showcase**: The new metric cards showing total requirements, high priority ones, AI overrides, and the chronologic recent activity stream.

### 2. Project View
- Click on one of the seeded projects (e.g., **Project Alpha Redesign**).
- **Showcase**: The list of existing requirements and participants.

### 3. Add Requirement & AI Suggestion
- Click **Add Requirement**.
- Fill out a title (e.g., "Add Google Analytics") and description ("Need to track user clicks").
- **AI Priority**: Click the **"Suggest AI Priority"** button.
- Wait a couple of seconds. Point out the AI suggestion preview card detailing the model's confidence and probabilities (LOW/MEDIUM/HIGH).
- Explicitly demonstrate the human-in-the-loop: manually change the priority from what the AI suggested to demonstrate the "Override" feature.
- **Rule-Based Effort**: Select "Low" for Complexity and "High" for Business Value. Click **"Suggest Effort Range"**.
- Explain how this is a deterministic rule-based calculation (not ML) that factors in priority, complexity, and adds a buffer for high business value. Note how it auto-fills the "Est. Effort (Days)".
- Click **Create Requirement**.

### 4. Exploring the Requirement Detail Page
- Click on the newly created requirement to view its details.
- **Showcase**:
  - The AI Priority Suggestion card, noting whether the priority was "Confirmed" or "Overridden".
  - The Effort Estimate card, explaining the rule-based calculation, and noting whether the human "Overridden" the suggested recommendation.
  - Update the Metadata: set complexity to "Low" and Business Value to "High", click **Update Metadata**.

### 5. Collaboration (Comments)
- Scroll down to the Comments section.
- Add a comment, e.g., "This should be easy since we already have the GA credentials."
- Notice how the Activity Log immediately records this action.

### 6. Review Actions (Approve / Reject / Request Changes)
- At the top/middle of the page, locate the **Review Requirement** section.
- Enter a reason like "Need to specify which GA version".
- Click **Request Changes**.
- Note the page reloads, the main status badge is now a yellow "Changes Requested", and the "Review Information" card displays the reason.

### 7. Activity Log Audit Trail
- Scroll down to the **Activity Log** card.
- Walk through the chronologic sequence:
  1. `requirement_created`
  2. `ai_priority_suggested`
  3. `priority_overridden` (or confirmed)
  4. `requirement_metadata_updated`
  5. `comment_added`
  6. `requirement_changes_requested`
- Explain how this provides a full, immutable audit trail of the requirement lifecycle, essential for enterprise change management.
