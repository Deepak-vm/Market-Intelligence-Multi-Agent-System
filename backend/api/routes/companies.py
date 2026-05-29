from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db.models import Company
from backend.pipeline.schemas import CompanyCreate, CompanyResponse

router = APIRouter(prefix="/api/companies", tags=["Watchlist Companies"])

@router.get("", response_model=List[CompanyResponse])
def get_watchlist(db: Session = Depends(get_db)):
    companies = db.query(Company).order_by(Company.name.asc()).all()
    res = []
    for c in companies:
        res.append(
            CompanyResponse(
                id=c.id,
                name=c.name,
                aliases=c.aliases or [],
                blog_rss=c.blog_rss,
                sec_cik=c.sec_cik,
                active=c.active,
                created_at=c.created_at.isoformat()
            )
        )
    return res

@router.post("", response_model=CompanyResponse)
def add_company(company_in: CompanyCreate, db: Session = Depends(get_db)):
    """Dynamically add a company name to the watchlist."""
    existing = db.query(Company).filter(Company.name.ilike(company_in.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Company already in watchlist")
    
    comp = Company(
        name=company_in.name.strip(),
        aliases=company_in.aliases or [company_in.name.lower()],
        blog_rss=company_in.blog_rss,
        sec_cik=company_in.sec_cik,
        active=True
    )
    db.add(comp)
    db.commit()
    db.refresh(comp)
    return CompanyResponse(
        id=comp.id,
        name=comp.name,
        aliases=comp.aliases or [],
        blog_rss=comp.blog_rss,
        sec_cik=comp.sec_cik,
        active=comp.active,
        created_at=comp.created_at.isoformat()
    )

@router.delete("/{company_id}")
def delete_company(company_id: int, db: Session = Depends(get_db)):
    comp = db.query(Company).filter(Company.id == company_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(comp)
    db.commit()
    return {"message": f"Company {comp.name} removed from watchlist"}
