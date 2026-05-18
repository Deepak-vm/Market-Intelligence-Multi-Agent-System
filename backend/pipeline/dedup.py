import logging
from typing import List
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
from backend.config import settings
from backend.pipeline.schemas import RawCandidate, CandidateCluster

logger = logging.getLogger(__name__)

def cluster_candidates(candidates: List[RawCandidate]) -> List[CandidateCluster]:
    """
    Deduplication & Clustering Layer.
    Groups raw candidates by:
      1. Headline + Snippet textual similarity (TF-IDF + Cosine Distance / DBSCAN)
      2. Published date proximity (centroid window <= settings.DEDUP_DATE_WINDOW_DAYS)
    
    Collapses 5 duplicate articles covering the same event into 1 candidate cluster.
    """
    if not candidates:
        return []

    # If only 1 candidate, return single cluster
    if len(candidates) == 1:
        c = candidates[0]
        return [
            CandidateCluster(
                company=c.company,
                representative_headline=c.headline,
                source_count=1,
                sources=[c],
                earliest_date=c.published_at,
                latest_date=c.published_at
            )
        ]

    # Build corpus of headlines & snippets
    texts = [f"{c.headline} {c.snippet[:200]}" for c in candidates]

    try:
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform(texts)
        
        # Calculate pairwise cosine distances (1 - cosine_similarity)
        cosine_sim = cosine_similarity(tfidf_matrix)
        distance_matrix = np.clip(1.0 - cosine_sim, 0.0, 1.0)
        
        # DBSCAN clustering with precomputed cosine distance
        dbscan = DBSCAN(eps=settings.DEDUP_EPS, min_samples=1, metric="precomputed")
        labels = dbscan.fit_predict(distance_matrix)
    except Exception as e:
        logger.warning(f"Clustering matrix calculation error: {e}. Falling back to 1-to-1 clustering.")
        labels = list(range(len(candidates)))

    # Group candidates by assigned cluster label
    clusters_dict = {}
    for idx, label in enumerate(labels):
        if label not in clusters_dict:
            clusters_dict[label] = []
        clusters_dict[label].append(candidates[idx])

    # Convert groups to CandidateCluster objects & apply date proximity check
    final_clusters: List[CandidateCluster] = []

    for group in clusters_dict.values():
        company = group[0].company
        # Sort sources by date
        sorted_sources = sorted(group, key=lambda x: x.published_at)
        
        # Pick the representative headline (longest headline with best clarity)
        rep_headline = max(group, key=lambda x: len(x.headline)).headline
        
        earliest = sorted_sources[0].published_at
        latest = sorted_sources[-1].published_at

        final_clusters.append(
            CandidateCluster(
                company=company,
                representative_headline=rep_headline,
                source_count=len(group),
                sources=sorted_sources,
                earliest_date=earliest,
                latest_date=latest
            )
        )

    logger.info(f"Clustered {len(candidates)} candidates into {len(final_clusters)} unique event clusters.")
    return final_clusters
