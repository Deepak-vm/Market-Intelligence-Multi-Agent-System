import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.agents.searcher import SearcherAgent
from backend.agents.analyst import AnalystAgent
from backend.pipeline.dedup import cluster_candidates
from backend.pipeline.verification import verify_and_route_event
from backend.db.models import IntelEventModel, EventSourceModel, ReviewQueueModel, ScanLogModel

logger = logging.getLogger(__name__)

class PipelineOrchestrator:
    """Coordinates Searcher, Dedup/Clustering, Analyst, Verification, and Database persistence."""

    def __init__(self):
        self.searcher = SearcherAgent()
        self.analyst = AnalystAgent()

    def run_pipeline(self, company: str, lookback_days: int, db: Session, scan_id: str = None) -> Dict[str, Any]:
        if not scan_id:
            scan_id = str(uuid.uuid4())

        # Initialize Scan Log
        scan_log = ScanLogModel(
            scan_id=scan_id,
            company=company,
            status="running",
            started_at=datetime.utcnow()
        )
        db.add(scan_log)
        db.commit()

        try:
            # Step 1: Searcher Agent (Recall focus)
            raw_candidates = self.searcher.execute_search(company, lookback_days)
            scan_log.raw_candidates = len(raw_candidates)

            # Step 2: Dedup / Clustering Layer
            clusters = cluster_candidates(raw_candidates)
            scan_log.clusters_formed = len(clusters)

            events_extracted = 0
            events_published = 0
            events_queued = 0

            # Step 3 & 4: Analyst Agent (Precision focus) & Verification Pass
            for cluster in clusters:
                intel_event = self.analyst.analyze_cluster(cluster)
                if not intel_event:
                    continue

                events_extracted += 1
                routed_event = verify_and_route_event(intel_event)

                if routed_event.status == "discarded":
                    continue

                # Save Intel Event to DB
                db_event = IntelEventModel(
                    company=routed_event.company,
                    event_type=routed_event.event_type,
                    event_date=routed_event.event_date,
                    confidence_score=routed_event.confidence_score,
                    confidence_rationale=routed_event.confidence_rationale,
                    status=routed_event.status,
                    details=routed_event.details,
                    created_at=datetime.utcnow()
                )
                db.add(db_event)
                db.flush()  # get db_event.id

                # Save Event Sources
                for s in cluster.sources:
                    db_source = EventSourceModel(
                        event_id=db_event.id,
                        url=s.url,
                        source_name=s.source_name,
                        headline=s.headline,
                        published_at=s.published_at
                    )
                    db.add(db_source)

                if routed_event.status == "auto_published":
                    events_published += 1
                elif routed_event.status == "pending_review":
                    events_queued += 1
                    # Create Human Review Queue item
                    review_item = ReviewQueueModel(
                        event_id=db_event.id,
                        reason=f"Single source ({routed_event.source_count}) or low confidence ({routed_event.confidence_score:.2f})"
                    )
                    db.add(review_item)

            # Update Scan Log status
            scan_log.status = "completed"
            scan_log.completed_at = datetime.utcnow()
            scan_log.events_extracted = events_extracted
            scan_log.events_published = events_published
            scan_log.events_queued = events_queued
            db.commit()

            return {
                "scan_id": scan_id,
                "company": company,
                "status": "completed",
                "raw_candidates": len(raw_candidates),
                "clusters": len(clusters),
                "events_extracted": events_extracted,
                "events_published": events_published,
                "events_queued": events_queued
            }

        except Exception as e:
            logger.error(f"Error running pipeline for {company}: {e}")
            scan_log.status = "failed"
            scan_log.completed_at = datetime.utcnow()
            db.commit()
            raise e
