import logging
from typing import List
from groq import Groq
from backend.config import settings
from backend.pipeline.schemas import RawCandidate
from backend.sources.gnews import search_gnews
from backend.sources.newsapi import search_newsapi
from backend.sources.sec_edgar import search_sec_edgar

logger = logging.getLogger(__name__)

# Core 4 event categories & search seed keywords
EVENT_CATEGORIES = {
    "funding": ["funding round raised valuation series investment investor"],
    "leadership": ["chief executive hired appointed departs steps down VP director join"],
    "product": ["launches unveils introduces features new tool model API release"],
    "layoff": ["layoffs restructuring cuts workforce reduction employees impacted"]
}

class SearcherAgent:
    """
    Searcher Agent: Focuses on RECALL.
    Uses LLM tool-use reasoning to expand search queries for target event types,
    hits multiple news and RSS sources, and gathers raw candidate signal.
    """
    
    def __init__(self):
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None

    def generate_search_queries(self, company: str) -> List[str]:
        """Uses Groq to generate intelligent event-specific search keywords per category."""
        if not self.groq_client:
            # Fallback to static seed queries if Groq key is not present
            return [
                "funding round raised valuation",
                "hired appointed steps down executive CEO CTO",
                "launches new product feature model",
                "layoffs workforce reduction restructuring cuts"
            ]

        try:
            prompt = (
                f"Generate 4 short, highly specific search queries to find recent events for company '{company}'.\n"
                f"Categories: 1) Funding rounds, 2) Leadership changes (hires/departures), 3) Product launches, 4) Layoffs.\n"
                f"Return ONLY 4 query strings, one per line, with no bullet points or extra text."
            )
            response = self.groq_client.chat.completions.create(
                model=settings.SEARCHER_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=150
            )
            text = response.choices[0].message.content or ""
            queries = [line.strip() for line in text.split("\n") if line.strip()]
            if len(queries) >= 4:
                return queries[:4]
        except Exception as e:
            logger.warning(f"Groq query expansion failed: {e}. Falling back to default keywords.")

        return [
            "funding raised valuation investor",
            "hired appointed steps down executive leadership",
            "launches product feature model announcement",
            "layoffs workforce reduction headcount cuts"
        ]

    def execute_search(self, company: str, lookback_days: int = 30) -> List[RawCandidate]:
        """Casts a wide net across all sources to maximize candidate recall."""
        queries = self.generate_search_queries(company)
        candidates: List[RawCandidate] = []
        seen_urls = set()

        for q in queries:
            # Source 1: GNews / Google News RSS (Free tier supported!)
            gnews_results = search_gnews(company, q)
            for cand in gnews_results:
                if cand.url not in seen_urls and cand.headline:
                    seen_urls.add(cand.url)
                    candidates.append(cand)

            # Source 2: NewsAPI (if configured)
            newsapi_results = search_newsapi(company, q)
            for cand in newsapi_results:
                if cand.url not in seen_urls and cand.headline:
                    seen_urls.add(cand.url)
                    candidates.append(cand)

        # Source 3: SEC EDGAR filings for financial/leadership signals
        sec_results = search_sec_edgar(company)
        for cand in sec_results:
            if cand.url not in seen_urls and cand.headline:
                seen_urls.add(cand.url)
                candidates.append(cand)

        logger.info(f"SearcherAgent gathered {len(candidates)} raw candidates for company: {company}")
        return candidates
