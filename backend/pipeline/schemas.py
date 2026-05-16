from datetime import datetime, date
from typing import List, Optional, Literal, Dict, Any, Union
from pydantic import BaseModel, Field

# --- Event Detail Schemas ---

class FundingEvent(BaseModel):
    amount_usd: Optional[float] = Field(None, description="Amount raised in USD if known")
    round_type: Optional[str] = Field(None, description="Round classification, e.g. Series A, Series B, Seed, Debt")
    lead_investor: Optional[str] = Field(None, description="Lead investor name if mentioned")
    valuation_usd: Optional[float] = Field(None, description="Valuation in USD if mentioned")

class LeadershipEvent(BaseModel):
    person_name: str = Field(..., description="Name of executive involved")
    role: str = Field(..., description="Executive role/title e.g. CEO, CTO, VP of Product")
    change_type: Literal["hire", "departure", "promotion"] = Field(..., description="Nature of leadership change")

class ProductEvent(BaseModel):
    product_name: str = Field(..., description="Name of the product or feature launched")
    launch_type: str = Field("launch", description="e.g. general availability, beta, major feature, acquisition")

class LayoffEvent(BaseModel):
    headcount_affected: Optional[int] = Field(None, description="Number of employees affected")
    percentage_workforce: Optional[float] = Field(None, description="Percentage of workforce affected (0-100)")
    departments: List[str] = Field(default_factory=list, description="Affected departments if mentioned")


# --- Pipeline Internal Schemas ---

class RawCandidate(BaseModel):
    company: str
    headline: str
    snippet: str
    url: str
    published_at: str  # ISO date YYYY-MM-DD
    source_name: str
    query_used: str

class CandidateCluster(BaseModel):
    company: str
    representative_headline: str
    source_count: int
    sources: List[RawCandidate]
    earliest_date: str
    latest_date: str

class IntelEvent(BaseModel):
    company: str
    event_type: Literal["funding", "leadership", "product", "layoff"]
    event_date: str
    confidence_score: float
    confidence_rationale: str
    source_count: int
    source_urls: List[str]
    details: Dict[str, Any]
    status: Literal["auto_published", "pending_review", "discarded"]


# --- API Request & Response DTOs ---

class CompanyCreate(BaseModel):
    name: str
    aliases: List[str] = Field(default_factory=list)
    blog_rss: Optional[str] = None
    sec_cik: Optional[str] = None

class CompanyResponse(BaseModel):
    id: int
    name: str
    aliases: List[str]
    blog_rss: Optional[str]
    sec_cik: Optional[str]
    active: bool
    created_at: str

    class Config:
        from_attributes = True

class EventResponse(BaseModel):
    id: int
    company: str
    event_type: str
    event_date: str
    confidence_score: float
    confidence_rationale: str
    status: str
    details: Dict[str, Any]
    sources: List[Dict[str, Any]]
    created_at: str

    class Config:
        from_attributes = True

class ScanTriggerRequest(BaseModel):
    company: Optional[str] = None  # If null, scans all active companies
    lookback_days: int = 30

class ScanStatusResponse(BaseModel):
    scan_id: str
    company: str
    status: str
    started_at: str
    completed_at: Optional[str] = None
    raw_candidates_found: int = 0
    clusters_formed: int = 0
    events_extracted: int = 0
    events_published: int = 0
    events_queued: int = 0

class ReviewActionRequest(BaseModel):
    reason: Optional[str] = None
