import httpx
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List
from datetime import datetime
from backend.config import settings
from backend.pipeline.schemas import RawCandidate

def search_gnews(company: str, event_keywords: str) -> List[RawCandidate]:
    """
    Hits GNews API if GNEWS_KEY is available.
    Otherwise falls back to Google News RSS search (which works 100% free with no API key!).
    """
    if settings.GNEWS_KEY:
        query = f'"{company}" {event_keywords}'
        url = f"https://gnews.io/api/v4/search?q={urllib.parse.quote(query)}&lang=en&token={settings.GNEWS_KEY}&max=10"
        try:
            resp = httpx.get(url, timeout=6.0)
            if resp.status_code == 200:
                data = resp.json()
                articles = data.get("articles", [])
                results = []
                for art in articles:
                    pub_date = (art.get("publishedAt") or "")[:10]
                    results.append(
                        RawCandidate(
                            company=company,
                            headline=art.get("title") or "",
                            snippet=art.get("description") or "",
                            url=art.get("url") or "",
                            published_at=pub_date or datetime.utcnow().strftime("%Y-%m-%d"),
                            source_name=art.get("source", {}).get("name", "GNews"),
                            query_used=query
                        )
                    )
                if results:
                    return results
        except Exception:
            pass

    # Free Fallback: Google News RSS
    return search_google_news_rss(company, event_keywords)


def search_google_news_rss(company: str, event_keywords: str) -> List[RawCandidate]:
    """Free Google News RSS feed parser that requires no API keys."""
    query = f'"{company}" {event_keywords}'
    encoded_query = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    
    results = []
    try:
        resp = httpx.get(rss_url, timeout=7.0, follow_redirects=True)
        if resp.status_code != 200:
            return []
        
        root = ET.fromstring(resp.text)
        channel = root.find("channel")
        if channel is None:
            return []
        
        for item in channel.findall("item"):
            title = item.findtext("title") or ""
            link = item.findtext("link") or ""
            pub_date_str = item.findtext("pubDate") or ""
            source_elem = item.find("source")
            source_name = source_elem.text if source_elem is not None and source_elem.text else "Google News RSS"
            
            # Parse publication date
            published_at = datetime.utcnow().strftime("%Y-%m-%d")
            if pub_date_str:
                try:
                    dt = datetime.strptime(pub_date_str[:25].strip(), "%a, %d %b %Y %H:%M:%S")
                    published_at = dt.strftime("%Y-%m-%d")
                except Exception:
                    pass
            
            results.append(
                RawCandidate(
                    company=company,
                    headline=title,
                    snippet=title,  # Google news RSS embeds headline/snippet together
                    url=link,
                    published_at=published_at,
                    source_name=source_name,
                    query_used=query
                )
            )
    except Exception:
        pass
    
    return results[:15]
