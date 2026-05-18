import httpx
import xml.etree.ElementTree as ET
from typing import List
from datetime import datetime
from backend.pipeline.schemas import RawCandidate

def search_sec_edgar(company: str) -> List[RawCandidate]:
    """Fetches SEC EDGAR filings (e.g. 8-K, S-1) for company via RSS feed."""
    url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company={company}&type=8-K&owner=include&count=10&output=atom"
    headers = {"User-Agent": "MarketIntelSystem admin@marketintel.com"}
    
    results = []
    try:
        resp = httpx.get(url, headers=headers, timeout=6.0)
        if resp.status_code != 200:
            return []
        
        root = ET.fromstring(resp.text)
        # Atom XML namespace handling
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entries = root.findall('atom:entry', ns) or root.findall('entry')
        
        for entry in entries:
            title = (entry.findtext('atom:title', default='', namespaces=ns) or entry.findtext('title') or '').strip()
            link_elem = entry.find('atom:link', ns) or entry.find('link')
            link = link_elem.attrib.get('href', '') if link_elem is not None else ''
            updated = (entry.findtext('atom:updated', default='', namespaces=ns) or entry.findtext('updated') or '')[:10]
            
            if title:
                results.append(
                    RawCandidate(
                        company=company,
                        headline=f"SEC Filing: {title}",
                        snippet=f"SEC EDGAR Official Filing for {company}. {title}",
                        url=link,
                        published_at=updated or datetime.utcnow().strftime("%Y-%m-%d"),
                        source_name="SEC EDGAR",
                        query_used="8-K"
                    )
                )
    except Exception:
        pass
    
    return results[:10]
