from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from app.core.database import get_session
from app.models.schema import ChangeRequest, Requirement, User, ChangeApproval, Comment, ChangeRequestStatus, ApprovalDecision
from app.api.schemas import ChangeRequestCreate, ApprovalDecisionCreate, CommentCreate

router = APIRouter(tags=["Change Requests & Comments"])

@router.post("/requirements/{requirement_id}/change-requests", status_code=status.HTTP_201_CREATED)
def create_change_request(requirement_id: int, cr: ChangeRequestCreate, session: Session = Depends(get_session)):
    req = session.get(Requirement, requirement_id)
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
        
    requester = session.get(User, cr.requested_by)
    if not requester:
        raise HTTPException(status_code=404, detail="Requester user not found")

    db_cr = ChangeRequest(
        requirement_id=requirement_id,
        project_id=req.project_id,
        title=cr.title,
        reason=cr.reason,
        requested_change=cr.requested_change,
        business_impact=cr.business_impact,
        technical_impact=cr.technical_impact,
        timeline_impact=cr.timeline_impact,
        cost_impact=cr.cost_impact,
        risk_level=cr.risk_level,
        requested_by=cr.requested_by
    )
    session.add(db_cr)
    session.commit()
    session.refresh(db_cr)
    return db_cr

@router.post("/change-requests/{change_request_id}/approve")
def approve_change_request(change_request_id: int, approval: ApprovalDecisionCreate, session: Session = Depends(get_session)):
    cr = session.get(ChangeRequest, change_request_id)
    if not cr:
        raise HTTPException(status_code=404, detail="Change request not found")
        
    approver = session.get(User, approval.approver_id)
    if not approver:
        raise HTTPException(status_code=404, detail="Approver user not found")
        
    if approval.decision not in [ApprovalDecision.approved, ApprovalDecision.rejected, ApprovalDecision.needs_clarification]:
        raise HTTPException(status_code=400, detail="Invalid decision")

    db_approval = ChangeApproval(
        change_request_id=change_request_id,
        approver_id=approval.approver_id,
        decision=approval.decision,
        remarks=approval.remarks
    )
    session.add(db_approval)
    
    # Update change request status based on decision
    if approval.decision == ApprovalDecision.approved:
        cr.status = ChangeRequestStatus.approved
    elif approval.decision == ApprovalDecision.rejected:
        cr.status = ChangeRequestStatus.rejected
        
    session.add(cr)
    session.commit()
    session.refresh(db_approval)
    return db_approval

@router.post("/requirements/{requirement_id}/comments")
def add_requirement_comment(requirement_id: int, comment: CommentCreate, session: Session = Depends(get_session)):
    req = session.get(Requirement, requirement_id)
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
        
    user = session.get(User, comment.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db_comment = Comment(
        user_id=comment.user_id,
        requirement_id=requirement_id,
        content=comment.content
    )
    session.add(db_comment)
    session.commit()
    session.refresh(db_comment)
    return db_comment

@router.post("/change-requests/{change_request_id}/comments")
def add_cr_comment(change_request_id: int, comment: CommentCreate, session: Session = Depends(get_session)):
    cr = session.get(ChangeRequest, change_request_id)
    if not cr:
        raise HTTPException(status_code=404, detail="Change request not found")
        
    user = session.get(User, comment.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db_comment = Comment(
        user_id=comment.user_id,
        change_request_id=change_request_id,
        content=comment.content
    )
    session.add(db_comment)
    session.commit()
    session.refresh(db_comment)
    return db_comment
