import json
import logging
import re
from typing import Optional
from groq import Groq
from backend.config import settings
from backend.pipeline.schemas import CandidateCluster, IntelEvent

logger = logging.getLogger(__name__)

ANALYST_SYSTEM_PROMPT = """
You are an expert Market Intelligence Analyst.
Your task is to analyze candidate article snippets about a company and classify if it is a real, confirmed event.

Target Event Types:
1. "funding": Funding rounds, venture raises, debt, IPO, valuation updates.
2. "leadership": Executive hires, resignations, board appointments, promotions (C-level, VP, Director).
3. "product": Product launches, new model releases, major feature rollouts, acquisitions.
4. "layoff": Headcount cuts, workforce reductions, office closures, restructuring.

Instructions:
- If the text is general news, commentary, rumor, stock market ticker update, or unconfirmed gossip, set "is_valid_event": false.
- If it matches one of the 4 types, set "is_valid_event": true and extract structured fields.
- Assign a confidence_score between 0.0 and 1.0 based on clarity and corroboration.
- Provide a brief confidence_rationale explaining why.

Return ONLY a JSON object with this exact structure:
{
  "is_valid_event": true/false,
  "event_type": "funding" | "leadership" | "product" | "layoff",
  "event_date": "YYYY-MM-DD",
  "confidence_score": 0.85,
  "confidence_rationale": "Explanation...",
  "details": {
     // event-type specific details
  }
}
"""

class AnalystAgent:
    """
    Analyst Agent: Focuses on PRECISION.
    Extracts typed event details, assigns confidence score and rationale,
    and returns a validated IntelEvent or None.
    """

    def __init__(self):
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None

    def analyze_cluster(self, cluster: CandidateCluster) -> Optional[IntelEvent]:
        """Analyzes a CandidateCluster and returns an IntelEvent if valid."""
        if not cluster.sources:
            return None

        # Build context from representative headline and snippets
        snippets_text = "\n".join([
            f"- [{s.source_name} | {s.published_at}] {s.headline}: {s.snippet}"
            for s in cluster.sources[:4]
        ])

        if self.groq_client:
            event = self._analyze_with_groq(cluster, snippets_text)
            if event:
                return event

        # Rule-based fallback extractor if Groq API key not set or call failed
        return self._analyze_with_heuristics(cluster, snippets_text)

    def _analyze_with_groq(self, cluster: CandidateCluster, snippets_text: str) -> Optional[IntelEvent]:
        try:
            prompt = (
                f"Company: {cluster.company}\n"
                f"Source Count: {cluster.source_count}\n"
                f"Representative Headline: {cluster.representative_headline}\n"
                f"Article Snippets:\n{snippets_text}\n"
            )
            response = self.groq_client.chat.completions.create(
                model=settings.ANALYST_MODEL,
                messages=[
                    {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=600
            )
            raw_text = response.choices[0].message.content or ""
            data = json.loads(raw_text)

            if not data.get("is_valid_event"):
                return None

            event_type = data.get("event_type")
            if event_type not in ["funding", "leadership", "product", "layoff"]:
                return None

            source_urls = [s.url for s in cluster.sources if s.url]

            return IntelEvent(
                company=cluster.company,
                event_type=event_type,
                event_date=data.get("event_date") or cluster.earliest_date,
                confidence_score=float(data.get("confidence_score", 0.7)),
                confidence_rationale=data.get("confidence_rationale", "Structured output extracted by Analyst Agent"),
                source_count=cluster.source_count,
                source_urls=source_urls,
                details=data.get("details", {}),
                status="pending_review"  # will be routed by verification step
            )
        except Exception as e:
            logger.warning(f"Groq Analyst Agent failed: {e}. Falling back to heuristic analysis.")
            return None

    def _analyze_with_heuristics(self, cluster: CandidateCluster, text: str) -> Optional[IntelEvent]:
        """Heuristic rule-based fallback to ensure system works offline / without API keys."""
        text_lower = (cluster.representative_headline + " " + text).lower()
        company = cluster.company
        source_urls = [s.url for s in cluster.sources if s.url]

        # 1. Funding
        if any(w in text_lower for w in ["funding", "raised", "valuation", "series a", "series b", "series c", "seed round"]):
            amount_match = re.search(r'\$(\d+(?:\.\d+)?\s*(?:million|billion|m|b)?)', text_lower)
            amount_str = amount_match.group(1) if amount_match else None
            return IntelEvent(
                company=company,
                event_type="funding",
                event_date=cluster.earliest_date,
                confidence_score=0.82 if cluster.source_count > 1 else 0.65,
                confidence_rationale=f"Reported funding event with {cluster.source_count} source(s).",
                source_count=cluster.source_count,
                source_urls=source_urls,
                details={"amount_usd": amount_str, "round_type": "Funding Round"},
                status="pending_review"
            )

        # 2. Leadership
        if any(w in text_lower for w in ["ceo", "cto", "cfo", "hired", "appointed", "joins", "steps down", "resigns", "vp of"]):
            change_type = "departure" if any(w in text_lower for w in ["steps down", "resigns", "leaves", "depart"]) else "hire"
            return IntelEvent(
                company=company,
                event_type="leadership",
                event_date=cluster.earliest_date,
                confidence_score=0.80 if cluster.source_count > 1 else 0.60,
                confidence_rationale=f"Detected executive change ({change_type}) across {cluster.source_count} source(s).",
                source_count=cluster.source_count,
                source_urls=source_urls,
                details={"person_name": "Executive", "role": "Executive Leadership", "change_type": change_type},
                status="pending_review"
            )

        # 3. Product
        if any(w in text_lower for w in ["launches", "unveils", "introduces", "announces new", "release", "gpt-4", "claude", "model"]):
            return IntelEvent(
                company=company,
                event_type="product",
                event_date=cluster.earliest_date,
                confidence_score=0.85 if cluster.source_count > 1 else 0.68,
                confidence_rationale=f"Product announcement corroborated by {cluster.source_count} source(s).",
                source_count=cluster.source_count,
                source_urls=source_urls,
                details={"product_name": cluster.representative_headline[:40], "launch_type": "launch"},
                status="pending_review"
            )

        # 4. Layoff
        if any(w in text_lower for w in ["layoff", "layoffs", "cuts workforce", "restructuring", "headcount reduction"]):
            return IntelEvent(
                company=company,
                event_type="layoff",
                event_date=cluster.earliest_date,
                confidence_score=0.88 if cluster.source_count > 1 else 0.70,
                confidence_rationale=f"Workforce reduction signal verified across {cluster.source_count} source(s).",
                source_count=cluster.source_count,
                source_urls=source_urls,
                details={"departments": ["General Workforce"]},
                status="pending_review"
            )

        return None
