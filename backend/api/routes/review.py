from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db.models import IntelEventModel, ReviewQueueModel
from backend.pipeline.schemas import ReviewActionRequest

router = APIRouter(prefix="/api/review", tags=["Human Review Queue"])

@router.get("", response_model=List[Dict[str, Any]])
def get_review_queue(db: Session = Depends(get_db)):
    """Fetch all pending review events flagged for human verification."""
    items = (
        db.query(ReviewQueueModel)
        .join(IntelEventModel)
        .filter(IntelEventModel.status == "pending_review")
        .all()
    )
    res = []
    for item in items:
        e = item.event
        res.append({
            "review_id": item.id,
            "event_id": e.id,
            "company": e.company,
            "event_type": e.event_type,
            "event_date": e.event_date,
            "confidence_score": e.confidence_score,
            "confidence_rationale": e.confidence_rationale,
            "reason_flagged": item.reason,
            "details": e.details or {},
            "sources": [
                {
                    "url": s.url,
                    "source_name": s.source_name,
                    "headline": s.headline,
                    "published_at": s.published_at
                }
                for s in e.sources
            ],
            "created_at": e.created_at.isoformat()
        })
    return res

@router.post("/{event_id}/approve")
def approve_event(event_id: int, action: ReviewActionRequest = None, db: Session = Depends(get_db)):
    """Approves a human-review event to auto_published."""
    e = db.query(IntelEventModel).filter(IntelEventModel.id == event_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Event not found")
    
    e.status = "auto_published"
    review_item = db.query(ReviewQueueModel).filter(ReviewQueueModel.event_id == event_id).first()
    if review_item:
        review_item.resolution = "approved"
        review_item.resolved_at = datetime.utcnow()
    
    db.commit()
    return {"message": f"Event {event_id} for {e.company} approved and published."}

@router.post("/{event_id}/reject")
def reject_event(event_id: int, action: ReviewActionRequest = None, db: Session = Depends(get_db)):
    """Rejects a human-review event and discards it."""
    e = db.query(IntelEventModel).filter(IntelEventModel.id == event_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Event not found")
    
    e.status = "discarded"
    review_item = db.query(ReviewQueueModel).filter(ReviewQueueModel.event_id == event_id).first()
    if review_item:
        review_item.resolution = "rejected"
        review_item.resolved_at = datetime.utcnow()
        if action and action.reason:
            review_item.reason = f"Rejected: {action.reason}"
    
    db.commit()
    return {"message": f"Event {event_id} for {e.company} rejected and discarded."}
