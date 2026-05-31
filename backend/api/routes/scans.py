import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from backend.db.database import get_db, SessionLocal
from backend.db.models import Company, ScanLogModel
from backend.agents.orchestrator import PipelineOrchestrator
from backend.pipeline.schemas import ScanTriggerRequest, ScanStatusResponse

router = APIRouter(prefix="/api/scans", tags=["Market Intelligence Scans"])
orchestrator = PipelineOrchestrator()

def run_background_scan(scan_id: str, company: str, lookback_days: int):
    """Background execution for pipeline scan."""
    db = SessionLocal()
    try:
        orchestrator.run_pipeline(company=company, lookback_days=lookback_days, db=db, scan_id=scan_id)
    except Exception as e:
        print(f"Background scan error for {company}: {e}")
    finally:
        db.close()

@router.post("/trigger")
def trigger_scan(req: ScanTriggerRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Triggers an on-demand scan for a dynamic company name or the entire watchlist."""
    scans_started = []

    if req.company:
        target_companies = [req.company]
    else:
        active_comps = db.query(Company).filter(Company.active == True).all()
        target_companies = [c.name for c in active_comps]

    if not target_companies:
        raise HTTPException(status_code=400, detail="No active companies to scan")

    for comp in target_companies:
        scan_id = str(uuid.uuid4())
        # Enqueue background task
        background_tasks.add_task(run_background_scan, scan_id, comp, req.lookback_days)
        scans_started.append({"scan_id": scan_id, "company": comp})

    return {
        "message": f"Enqueued scan for {len(scans_started)} company(ies)",
        "scans": scans_started
    }

@router.get("/{scan_id}", response_model=ScanStatusResponse)
def get_scan_status(scan_id: str, db: Session = Depends(get_db)):
    scan = db.query(ScanLogModel).filter(ScanLogModel.scan_id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan ID not found")
    
    return ScanStatusResponse(
        scan_id=scan.scan_id,
        company=scan.company,
        status=scan.status,
        started_at=scan.started_at.isoformat(),
        completed_at=scan.completed_at.isoformat() if scan.completed_at else None,
        raw_candidates_found=scan.raw_candidates or 0,
        clusters_formed=scan.clusters_formed or 0,
        events_extracted=scan.events_extracted or 0,
        events_published=scan.events_published or 0,
        events_queued=scan.events_queued or 0
    )

@router.get("", response_model=List[ScanStatusResponse])
def list_scans(limit: int = 20, db: Session = Depends(get_db)):
    scans = db.query(ScanLogModel).order_by(ScanLogModel.started_at.desc()).limit(limit).all()
    res = []
    for scan in scans:
        res.append(
            ScanStatusResponse(
                scan_id=scan.scan_id,
                company=scan.company,
                status=scan.status,
                started_at=scan.started_at.isoformat(),
                completed_at=scan.completed_at.isoformat() if scan.completed_at else None,
                raw_candidates_found=scan.raw_candidates or 0,
                clusters_formed=scan.clusters_formed or 0,
                events_extracted=scan.events_extracted or 0,
                events_published=scan.events_published or 0,
                events_queued=scan.events_queued or 0
            )
        )
    return res
