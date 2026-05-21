import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.db.database import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    aliases = Column(JSON, default=list)
    blog_rss = Column(String, nullable=True)
    sec_cik = Column(String, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class IntelEventModel(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String, index=True, nullable=False)
    event_type = Column(String, index=True, nullable=False)  # funding, leadership, product, layoff
    event_date = Column(String, nullable=False)
    confidence_score = Column(Float, nullable=False)
    confidence_rationale = Column(Text, nullable=False)
    status = Column(String, index=True, nullable=False)  # auto_published, pending_review, discarded
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    sources = relationship("EventSourceModel", back_populates="event", cascade="all, delete-orphan")
    review_item = relationship("ReviewQueueModel", back_populates="event", uselist=False, cascade="all, delete-orphan")

class EventSourceModel(Base):
    __tablename__ = "event_sources"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    url = Column(String, nullable=False)
    source_name = Column(String, nullable=False)
    headline = Column(String, nullable=False)
    published_at = Column(String, nullable=False)

    event = relationship("IntelEventModel", back_populates="sources")

class ReviewQueueModel(Base):
    __tablename__ = "review_queue"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, unique=True)
    reason = Column(Text, nullable=True)
    resolution = Column(String, nullable=True)  # approved, rejected
    resolved_at = Column(DateTime, nullable=True)

    event = relationship("IntelEventModel", back_populates="review_item")

class ScanLogModel(Base):
    __tablename__ = "scan_logs"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(String, unique=True, index=True, nullable=False)
    company = Column(String, nullable=False)
    status = Column(String, nullable=False)  # running, completed, failed
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    raw_candidates = Column(Integer, default=0)
    clusters_formed = Column(Integer, default=0)
    events_extracted = Column(Integer, default=0)
    events_published = Column(Integer, default=0)
    events_queued = Column(Integer, default=0)
