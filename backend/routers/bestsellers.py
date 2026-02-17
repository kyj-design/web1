"""
Bestsellers Router - 베스트셀러 분석 API
"""
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import BestsellerTemplate, get_db
from ..services.etsy_service import etsy_service
from ..services.image_analysis_service import image_analysis_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Pydantic 스키마 ──────────────────────────────────

class BestsellerSearchRequest(BaseModel):
    keyword: str
    limit: int = 10
    analyze_images: bool = True


# ── 헬퍼 함수 ──────────────────────────────────────

def _template_to_dict(t: BestsellerTemplate) -> dict:
    return {
        "id": t.id,
        "etsy_listing_id": t.etsy_listing_id,
        "title": t.title,
        "seller_name": t.seller_name,
        "price": t.price,
        "reviews_count": t.reviews_count,
        "sales_count": t.sales_count,
        "image_url": t.image_url,
        "color_palette": t.color_palette,
        "style": t.style,
        "layout_data": t.layout_data,
        "keywords": t.keywords,
        "analyzed_at": t.analyzed_at.isoformat() if t.analyzed_at else None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


# ── 백그라운드 태스크 ──────────────────────────────────

async def _analyze_template_image(template_id: int, image_url: str):
    """
    백그라운드 태스크: 이미지 분석 후 DB 업데이트.
    BackgroundTasks는 응답 후 실행되므로 독립적인 DB 세션 사용.
    """
    from ..database import SessionLocal
    from datetime import datetime

    db = SessionLocal()
    try:
        analysis = await image_analysis_service.download_and_analyze(image_url)
        template = db.query(BestsellerTemplate).filter(
            BestsellerTemplate.id == template_id
        ).first()

        if template and analysis.get("success"):
            template.color_palette = analysis["color_palette"]
            template.style = analysis["dominant_style"]
            template.layout_data = analysis["layout_data"]
            template.analyzed_at = datetime.utcnow()
            db.commit()
            logger.info(f"Image analysis completed for template {template_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Background image analysis failed for template {template_id}: {e}")
    finally:
        db.close()


# ── 엔드포인트 ──────────────────────────────────────

@router.post("/analyze")
async def analyze_bestsellers(
    request: BestsellerSearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    키워드로 베스트셀러 검색 후 분석 시작.
    이미지 분석은 BackgroundTasks로 비동기 처리.

    POST /api/bestsellers/analyze
    Body: {"keyword": "digital planner", "limit": 10, "analyze_images": true}

    반환: 즉시 저장된 BestsellerTemplate 목록 (이미지 분석 전)
    이미지 분석 완료 후 GET /api/bestsellers/ 로 폴링하여 결과 확인
    """
    if not request.keyword.strip():
        raise HTTPException(status_code=400, detail="Keyword cannot be empty")

    search_result = await etsy_service.search_listings(
        keywords=request.keyword.strip(),
        limit=request.limit,
        sort_on="score",
    )
    listings = search_result.get("results", [])

    if not listings:
        raise HTTPException(status_code=404, detail="No bestsellers found")

    saved_templates = []
    for listing in listings:
        existing = db.query(BestsellerTemplate).filter(
            BestsellerTemplate.etsy_listing_id == str(listing["listing_id"])
        ).first()

        if existing:
            saved_templates.append(existing)
            continue

        price_data = listing.get("price", {})
        divisor = price_data.get("divisor", 100) or 100
        price = price_data.get("amount", 0) / divisor

        image_url = None
        if listing.get("images"):
            image_url = listing["images"][0].get("url_570xN")

        template = BestsellerTemplate(
            etsy_listing_id=str(listing["listing_id"]),
            title=listing.get("title", ""),
            seller_name=listing.get("seller_name", ""),
            price=price,
            reviews_count=listing.get("num_favorers", 0),
            sales_count=0,
            image_url=image_url,
            keywords=listing.get("tags", []),
        )
        db.add(template)
        db.flush()
        saved_templates.append(template)

    db.commit()
    for t in saved_templates:
        db.refresh(t)

    if request.analyze_images:
        for template in saved_templates:
            if template.image_url and not template.color_palette:
                background_tasks.add_task(
                    _analyze_template_image,
                    template_id=template.id,
                    image_url=template.image_url,
                )

    return {
        "message": (
            f"{len(saved_templates)} bestsellers saved. "
            "Image analysis running in background."
        ),
        "count": len(saved_templates),
        "templates": [_template_to_dict(t) for t in saved_templates],
    }


@router.get("/")
def list_bestsellers(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    style: Optional[str] = Query(None),
    analyzed_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    """
    베스트셀러 목록 조회 (필터링 지원).
    GET /api/bestsellers/?style=minimal&analyzed_only=true
    """
    query = db.query(BestsellerTemplate)

    if style:
        query = query.filter(BestsellerTemplate.style == style)
    if analyzed_only:
        query = query.filter(BestsellerTemplate.color_palette.isnot(None))

    total = query.count()
    templates = (
        query.order_by(BestsellerTemplate.reviews_count.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "templates": [_template_to_dict(t) for t in templates],
    }


@router.get("/stats")
def get_bestseller_stats(db: Session = Depends(get_db)):
    """
    대시보드용 베스트셀러 요약 통계.
    GET /api/bestsellers/stats
    """
    total = db.query(BestsellerTemplate).count()
    analyzed = db.query(BestsellerTemplate).filter(
        BestsellerTemplate.color_palette.isnot(None)
    ).count()

    style_dist_rows = (
        db.query(BestsellerTemplate.style, func.count(BestsellerTemplate.id))
        .filter(BestsellerTemplate.style.isnot(None))
        .group_by(BestsellerTemplate.style)
        .all()
    )
    style_distribution = {style: count for style, count in style_dist_rows}

    return {
        "total": total,
        "analyzed": analyzed,
        "pending_analysis": total - analyzed,
        "style_distribution": style_distribution,
    }
