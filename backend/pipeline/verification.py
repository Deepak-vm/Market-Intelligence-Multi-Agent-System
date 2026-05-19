import logging
from backend.config import settings
from backend.pipeline.schemas import IntelEvent

logger = logging.getLogger(__name__)

def verify_and_route_event(event: IntelEvent) -> IntelEvent:
    """
    Verification & Routing Pass.
    
    Rules:
      1. Discard if confidence < DISCARD_CONFIDENCE_FLOOR (0.40)
      2. Auto-publish if source_count >= AUTO_PUBLISH_MIN_SOURCES (2) AND confidence_score >= AUTO_PUBLISH_CONFIDENCE_THRESHOLD (0.75)
      3. Flag for Human Review Queue if single source OR low confidence.
    """
    if event.confidence_score < settings.DISCARD_CONFIDENCE_FLOOR:
        event.status = "discarded"
        logger.info(f"Event discarded due to low confidence ({event.confidence_score:.2f}): {event.company} {event.event_type}")
        return event

    if (
        event.source_count >= settings.AUTO_PUBLISH_MIN_SOURCES
        and event.confidence_score >= settings.AUTO_PUBLISH_CONFIDENCE_THRESHOLD
    ):
        event.status = "auto_published"
        logger.info(f"Event AUTO-PUBLISHED ({event.confidence_score:.2f}, {event.source_count} sources): {event.company} {event.event_type}")
    else:
        event.status = "pending_review"
        logger.info(f"Event routed to HUMAN REVIEW QUEUE ({event.confidence_score:.2f}, {event.source_count} sources): {event.company} {event.event_type}")

    return event
