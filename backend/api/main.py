from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.db.database import init_db
from backend.api.routes import events, companies, review, scans, metrics

app = FastAPI(
    title="Market Intelligence Multi-Agent System API",
    description="Backend API for two-agent (Searcher + Analyst) market intelligence pipeline",
    version="1.0.0"
)

# Enable CORS for local React dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(events.router)
app.include_router(companies.router)
app.include_router(review.router)
app.include_router(scans.router)
app.include_router(metrics.router)

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
def root():
    return {
        "status": "online",
        "system": "Market Intelligence Multi-Agent Pipeline",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)
