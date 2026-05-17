import feedparser
from typing import List, Optional
from datetime import datetime
from backend.pipeline.schemas import RawCandidate

def fetch_rss_feed(feed_url: str, company: str, source_label: str = "RSS") -> List[RawCandidate]:
    """Parses arbitrary RSS/Atom feeds using feedparser."""
    results = []
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:15]:
            title = getattr(entry, "title", "")
            summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
            link = getattr(entry, "link", "")
            
            published_at = datetime.utcnow().strftime("%Y-%m-%d")
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published_at = datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d")
            
            results.append(
                RawCandidate(
                    company=company,
                    headline=title,
                    snippet=summary[:300] if summary else title,
                    url=link,
                    published_at=published_at,
                    source_name=source_label,
                    query_used=feed_url
                )
            )
    except Exception:
        pass
    return results
