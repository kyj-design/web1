"""
Listings Router - SEO 콘텐츠 생성 + Etsy 리스팅 관리 API
"""
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import CanvaTemplate, SEOContent, EtsyListing, get_db
from ..services.seo_service import seo_service
from ..services.listing_service import listing_service

router = APIRouter()


# ── Pydantic 스키마 ──────────────────────────────────

class ListingCreate(BaseModel):
    template_id: int
    seo_id: int
    price: float = Field(default=4.99, ge=0.20)
    pdf_id: Optional[int] = None


class ListingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    price: Optional[float] = Field(default=None, ge=0.20)
    status: Optional[str] = None


# ── SEO 콘텐츠 생성 ──────────────────────────────────

@router.post("/seo/generate")
async def generate_seo(
    template_id: int,
    db: Session = Depends(get_db),
):
    """
    LLM으로 SEO 콘텐츠(제목/설명/태그) 생성.
    POST /api/listings/seo/generate?template_id={id}

    Ollama가 실행 중이면 LLM을 사용하고, 아니면 fallback 콘텐츠를 반환합니다.
    """
    template = db.query(CanvaTemplate).filter(CanvaTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    seo = await seo_service.generate_seo_content(template_id, db)
    return seo_service.seo_to_dict(seo)


@router.get("/seo/{template_id}")
def list_seo(
    template_id: int,
    db: Session = Depends(get_db),
):
    """
    템플릿에 대해 생성된 SEO 버전 목록 조회.
    GET /api/listings/seo/{template_id}
    """
    template = db.query(CanvaTemplate).filter(CanvaTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    seos = (
        db.query(SEOContent)
        .filter(SEOContent.template_id == template_id)
        .order_by(SEOContent.version.desc())
        .all()
    )
    return {
        "template_id": template_id,
        "template_name": template.name,
        "seo_versions": [seo_service.seo_to_dict(s) for s in seos],
    }


@router.delete("/seo/{seo_id}")
def delete_seo(seo_id: int, db: Session = Depends(get_db)):
    """SEO 버전 삭제."""
    seo = db.query(SEOContent).filter(SEOContent.id == seo_id).first()
    if not seo:
        raise HTTPException(status_code=404, detail="SEO content not found")
    db.delete(seo)
    db.commit()
    return {"message": f"SEO content {seo_id} deleted"}


# ── 리스팅 CRUD ──────────────────────────────────────

@router.post("/")
def create_listing(
    data: ListingCreate,
    db: Session = Depends(get_db),
):
    """
    SEO 콘텐츠를 선택하여 Draft 리스팅 생성.
    POST /api/listings/
    """
    try:
        listing = listing_service.create_listing(
            template_id=data.template_id,
            seo_id=data.seo_id,
            price=data.price,
            pdf_id=data.pdf_id,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return listing_service.listing_to_dict(listing, with_template=True)


@router.get("/")
def list_listings(
    template_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    리스팅 목록 조회.
    GET /api/listings/?status=draft&template_id=1
    """
    result = listing_service.list_listings(
        template_id=template_id,
        status=status,
        skip=skip,
        limit=limit,
        db=db,
    )
    return {
        "total": result["total"],
        "listings": [
            listing_service.listing_to_dict(l, with_template=True)
            for l in result["listings"]
        ],
    }


@router.get("/stats")
def get_listing_stats(db: Session = Depends(get_db)):
    """
    대시보드용 리스팅 통계.
    GET /api/listings/stats
    """
    return listing_service.get_stats(db)


@router.get("/{listing_id}")
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    """단일 리스팅 상세 조회."""
    listing = db.query(EtsyListing).filter(EtsyListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing_service.listing_to_dict(listing, with_template=True)


@router.put("/{listing_id}")
def update_listing(
    listing_id: int,
    data: ListingUpdate,
    db: Session = Depends(get_db),
):
    """리스팅 수정 (제목, 태그, 가격, 상태 등)."""
    listing = listing_service.update_listing(
        listing_id=listing_id,
        title=data.title,
        description=data.description,
        tags=data.tags,
        price=data.price,
        status=data.status,
        db=db,
    )
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing_service.listing_to_dict(listing, with_template=True)


@router.delete("/{listing_id}")
def delete_listing(listing_id: int, db: Session = Depends(get_db)):
    """리스팅 삭제."""
    success = listing_service.delete_listing(listing_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Listing not found")
    return {"message": f"Listing {listing_id} deleted"}


# ── Etsy API 업로드 ──────────────────────────────────

@router.post("/{listing_id}/publish")
async def publish_listing(
    listing_id: int,
    db: Session = Depends(get_db),
):
    """
    Etsy API로 리스팅 업로드 (draft → published).
    POST /api/listings/{listing_id}/publish

    - Etsy API 키 미설정 시: Mock 모드로 가짜 ID를 발급합니다.
    - 실제 연동 시: OAuth 설정 후 shop_id를 etsy_service에 전달해야 합니다.
    """
    try:
        listing = await listing_service.publish_to_etsy(listing_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    from ..services.etsy_service import etsy_service as _etsy_svc
    return {
        "message": "Listing published to Etsy",
        "listing": listing_service.listing_to_dict(listing, with_template=True),
        "is_mock": _etsy_svc._use_mock,
    }
