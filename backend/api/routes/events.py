from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db.models import IntelEventModel
from backend.pipeline.schemas import EventResponse

router = APIRouter(prefix="/api/events", tags=["Events"])

@router.get("", response_model=List[EventResponse])
def list_events(
    company: Optional[str] = None,
    event_type: Optional[str] = None,
    status: Optional[str] = Query(None, description="auto_published, pending_review, or discarded"),
    db: Session = Depends(get_db)
):
    query = db.query(IntelEventModel)
    if company:
        query = query.filter(IntelEventModel.company.ilike(f"%{company}%"))
    if event_type:
        query = query.filter(IntelEventModel.event_type == event_type)
    if status:
        query = query.filter(IntelEventModel.status == status)
    
    events = query.order_by(IntelEventModel.created_at.desc()).all()
    
    res = []
    for e in events:
        sources_list = [
            {
                "id": s.id,
                "url": s.url,
                "source_name": s.source_name,
                "headline": s.headline,
                "published_at": s.published_at
            }
            for s in e.sources
        ]
        res.append(
            EventResponse(
                id=e.id,
                company=e.company,
                event_type=e.event_type,
                event_date=e.event_date,
                confidence_score=e.confidence_score,
                confidence_rationale=e.confidence_rationale,
                status=e.status,
                details=e.details or {},
                sources=sources_list,
                created_at=e.created_at.isoformat()
            )
        )
    return res

@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    e = db.query(IntelEventModel).filter(IntelEventModel.id == event_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Event not found")
    
    sources_list = [
        {
            "id": s.id,
            "url": s.url,
            "source_name": s.source_name,
            "headline": s.headline,
            "published_at": s.published_at
        }
        for s in e.sources
    ]
    return EventResponse(
        id=e.id,
        company=e.company,
        event_type=e.event_type,
        event_date=e.event_date,
        confidence_score=e.confidence_score,
        confidence_rationale=e.confidence_rationale,
        status=e.status,
        details=e.details or {},
        sources=sources_list,
        created_at=e.created_at.isoformat()
    )
