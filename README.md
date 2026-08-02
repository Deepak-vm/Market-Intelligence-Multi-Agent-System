# Market Intelligence Multi-Agent System

A multi-agent market & competitor intelligence system (Searcher + Analyst agents) that monitors public signal (News, RSS, SEC filings) across a configurable company watchlist and converts raw noisy text into typed, deduplicated, verified market events.

---

## Key Features

- **Searcher Agent (Groq Tool-Use)**: Casts a wide net across NewsAPI, GNews, Google News RSS, and SEC EDGAR filings to maximize candidate recall.
- **Deduplication & Clustering Layer**: Sentence/TF-IDF text embeddings + DBSCAN cosine distance clustering + date-proximity window merging. Group duplicate stories before hitting the Analyst.
- **Analyst Agent (Structured Output + Confidence)**: Classifies candidates into 4 strict categories (`funding`, `leadership`, `product`, `layoff`), extracts Pydantic typed fields, and assigns confidence scores with rationale.
- **Verification & Human-in-the-Loop Queue**: Corroborates cross-source event claims. High confidence & corroborated events auto-publish; single-source or low-confidence claims route to a Human Review Queue.
- **Dynamic Watchlist Management**: Users can dynamically add and manage companies to monitor without hardcoding.
- **Evaluation Harness & Benchmark**: Ground-truth dataset with precision/recall reporting per category and blended overall.

---

## Architecture Overview

```
Watchlist (Dynamic Companies DB)
        │
        ▼
┌────────────────────────┐     ┌──────────────────────┐     ┌────────────────────────┐
│     Searcher Agent     │────▶│   Dedup / Cluster    │────▶│     Analyst Agent      │
│     (Groq Tool-Use)    │     │   (TF-IDF + DBSCAN   │     │  (Groq Structured Out) │
│     • News / GNews RSS │     │    Cosine Distance)  │     │  • Typed event extraction│
│     • SEC EDGAR RSS    │     │  group duplicate     │     │  • Confidence + rationale│
└────────────────────────┘     │  article candidate   │     └───────────┬────────────┘
                               └──────────────────────┘                 │
                                                               ┌────────▼────────┐
                                                               │  Verification   │
                                                               │  Pass & Routing │
                                                               └────────┬────────┘
                                                                        │
                                           ┌────────────────────────────┴────────────────────────────┐
                                           │                                                         │
                                 ┌─────────▼─────────┐                                     ┌─────────▼─────────┐
                                 │   Auto-Published  │                                     │ Human Review Queue│
                                 │ (Corroborated ≥2) │                                     │  (Single Source)  │
                                 └─────────┬─────────┘                                     └─────────┬─────────┘
                                           │                                                         │
                                           └────────────────────────────┬────────────────────────────┘
                                                                        │
                                                           ┌────────────▼────────────┐
                                                           │ PostgreSQL/SQLite DB    │
                                                           │ + React Dashboard UI    │
                                                           └─────────────────────────┘
```

---

## Quickstart Guide

### 1. Backend Setup

```bash
# Activate virtual environment
source venv/bin/activate

# Install requirements
pip install -r backend/requirements.txt

# Run FastAPI backend
python -m backend.api.main
```
Backend API will be running on `http://localhost:8000`.

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```
Dashboard UI will be running on `http://localhost:3000`.

---

## Evaluation Benchmark

Run the ground-truth benchmark to measure precision and recall across event categories:

```bash
python eval/run_eval.py
```

### Benchmark Results Overview

| Event Category | Precision | Recall | F1 Score |
|---|---|---|---|
| **Funding** | 91.0% | 84.0% | 87.4% |
| **Leadership** | 76.0% | 71.0% | 73.4% |
| **Product** | 82.0% | 79.0% | 80.5% |
| **Layoffs** | 88.0% | 82.0% | 84.9% |
| **BLENDED OVERALL** | **84.25%** | **79.0%** | **81.5%** |

- **Auto-Publish Rate**: 68.0%
- **Routed to Human Review Queue**: 32.0%
- **Deduplication Cluster Accuracy**: 92.5%
