"""
Market Research Router - Niche 조사 및 키워드 분석 API
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import Keyword, Niche, get_db
from ..services.market_research_service import market_research_service

router = APIRouter()


# ── Pydantic 스키마 ──────────────────────────────────

class ResearchRequest(BaseModel):
    keyword: str
    limit: int = 25


# ── 엔드포인트 ──────────────────────────────────────

@router.post("/research")
async def research_keyword(
    request: ResearchRequest,
    db: Session = Depends(get_db),
):
    """
    키워드 기반 시장 조사 실행.
    POST /api/market/research
    Body: {"keyword": "digital planner", "limit": 25}
    """
    if not request.keyword.strip():
        raise HTTPException(status_code=400, detail="Keyword cannot be empty")

    result = await market_research_service.research_keyword(
        keyword=request.keyword.strip(),
        db=db,
        limit=request.limit,
    )

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/niches")
def list_niches(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("trend_score"),
    db: Session = Depends(get_db),
):
    """
    저장된 Niche 목록 조회.
    GET /api/market/niches?skip=0&limit=20&sort_by=trend_score

    sort_by 옵션: trend_score | profit_potential_score | avg_price | search_volume
    """
    valid_sort_columns = {
        "trend_score": Niche.trend_score,
        "profit_potential_score": Niche.profit_potential_score,
        "avg_price": Niche.avg_price,
        "search_volume": Niche.search_volume,
    }
    sort_column = valid_sort_columns.get(sort_by, Niche.trend_score)

    niches = (
        db.query(Niche)
        .order_by(sort_column.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    total = db.query(Niche).count()

    return {
        "total": total,
        "niches": [market_research_service._niche_to_dict(n) for n in niches],
    }


@router.get("/niches/{niche_id}")
def get_niche(niche_id: int, db: Session = Depends(get_db)):
    """
    특정 Niche 상세 조회 (키워드 포함).
    GET /api/market/niches/{niche_id}
    """
    niche = db.query(Niche).filter(Niche.id == niche_id).first()
    if not niche:
        raise HTTPException(status_code=404, detail="Niche not found")

    keywords = db.query(Keyword).filter(Keyword.niche_id == niche_id).all()
    return {
        "niche": market_research_service._niche_to_dict(niche),
        "keywords": [market_research_service._keyword_to_dict(k) for k in keywords],
    }


@router.delete("/niches/{niche_id}")
def delete_niche(niche_id: int, db: Session = Depends(get_db)):
    """
    Niche 삭제 (cascade: 연관 Keywords도 삭제).
    DELETE /api/market/niches/{niche_id}
    """
    niche = db.query(Niche).filter(Niche.id == niche_id).first()
    if not niche:
        raise HTTPException(status_code=404, detail="Niche not found")
    db.delete(niche)
    db.commit()
    return {"message": f"Niche '{niche.name}' deleted"}


@router.get("/stats")
def get_market_stats(db: Session = Depends(get_db)):
    """
    대시보드용 시장 조사 요약 통계.
    GET /api/market/stats
    """
    total_niches = db.query(Niche).count()
    total_keywords = db.query(Keyword).count()

    top_niches = (
        db.query(Niche)
        .order_by(Niche.profit_potential_score.desc())
        .limit(5)
        .all()
    )

    return {
        "total_niches": total_niches,
        "total_keywords": total_keywords,
        "top_niches": [market_research_service._niche_to_dict(n) for n in top_niches],
    }
