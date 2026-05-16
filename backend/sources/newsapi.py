import httpx
from typing import List
from backend.config import settings
from backend.pipeline.schemas import RawCandidate

def search_newsapi(company: str, event_keywords: str) -> List[RawCandidate]:
    """Hits NewsAPI if key is configured, otherwise returns empty list (fallback to RSS)."""
    if not settings.NEWSAPI_KEY:
        return []
    
    query = f"{company} {event_keywords}".strip()
    url = f"https://newsapi.org/v2/everything?q={query}&apiKey={settings.NEWSAPI_KEY}&sortBy=publishedAt&pageSize=15"
    
    try:
        resp = httpx.get(url, timeout=5.0)
        if resp.status_code != 200:
            return []
        data = resp.json()
        articles = data.get("articles", [])
        results = []
        for art in articles:
            results.append(
                RawCandidate(
                    company=company,
                    headline=art.get("title") or "",
                    snippet=art.get("description") or art.get("content") or "",
                    url=art.get("url") or "",
                    published_at=(art.get("publishedAt") or "")[:10],
                    source_name=art.get("source", {}).get("name", "NewsAPI"),
                    query_used=query
                )
            )
        return results
    except Exception:
        return []
