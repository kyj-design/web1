"""
Listing Service - Etsy 리스팅 생성/관리
SEO 콘텐츠 선택 → EtsyListing DB 저장 → Etsy API 업로드
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import CanvaTemplate, DeliveryPDF, EtsyListing, SEOContent
from ..services.etsy_service import etsy_service

logger = logging.getLogger(__name__)

DEFAULT_PRICE = 4.99
LISTING_STATUS = ("draft", "published", "deactivated")


class ListingService:
    """Etsy 리스팅 CRUD 및 Etsy API 업로드 서비스"""

    # ── 리스팅 생성 ─────────────────────────────────

    def create_listing(
        self,
        template_id: int,
        seo_id: int,
        price: float = DEFAULT_PRICE,
        pdf_id: Optional[int] = None,
        db: Session = None,
    ) -> EtsyListing:
        """
        SEO 콘텐츠를 선택하여 EtsyListing draft를 생성.
        """
        template = db.query(CanvaTemplate).filter(CanvaTemplate.id == template_id).first()
        if not template:
            raise ValueError(f"Template {template_id} not found")

        seo = db.query(SEOContent).filter(SEOContent.id == seo_id).first()
        if not seo:
            raise ValueError(f"SEO content {seo_id} not found")

        if pdf_id:
            pdf = db.query(DeliveryPDF).filter(
                DeliveryPDF.id == pdf_id,
                DeliveryPDF.template_id == template_id,
            ).first()
            if not pdf:
                pdf_id = None

        listing = EtsyListing(
            template_id=template_id,
            pdf_id=pdf_id,
            title=seo.title,
            description=seo.description,
            tags=seo.tags,
            price=price,
            status="draft",
        )
        db.add(listing)
        db.commit()
        db.refresh(listing)
        logger.info(f"Listing created: {listing.id} (template={template_id})")
        return listing

    # ── 수정 ────────────────────────────────────────

    def update_listing(
        self,
        listing_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[list] = None,
        price: Optional[float] = None,
        status: Optional[str] = None,
        db: Session = None,
    ) -> Optional[EtsyListing]:
        listing = db.query(EtsyListing).filter(EtsyListing.id == listing_id).first()
        if not listing:
            return None

        if title is not None:
            listing.title = title[:140]
        if description is not None:
            listing.description = description
        if tags is not None:
            listing.tags = [t[:20] for t in tags[:13]]
        if price is not None:
            listing.price = max(0.20, price)
        if status is not None and status in LISTING_STATUS:
            listing.status = status

        db.commit()
        db.refresh(listing)
        return listing

    def delete_listing(self, listing_id: int, db: Session) -> bool:
        listing = db.query(EtsyListing).filter(EtsyListing.id == listing_id).first()
        if not listing:
            return False
        db.delete(listing)
        db.commit()
        return True

    # ── Etsy API 업로드 ─────────────────────────────

    async def publish_to_etsy(
        self,
        listing_id: int,
        db: Session,
    ) -> EtsyListing:
        """
        EtsyListing을 Etsy API로 업로드.
        Mock 모드에서는 가짜 ID를 반환합니다.
        """
        listing = db.query(EtsyListing).filter(EtsyListing.id == listing_id).first()
        if not listing:
            raise ValueError(f"Listing {listing_id} not found")

        result = await etsy_service.create_draft_listing(
            title=listing.title,
            description=listing.description,
            tags=listing.tags,
            price=listing.price,
        )

        # etsy_listing_id 저장 및 상태 업데이트
        listing.etsy_listing_id = str(result.get("listing_id", ""))
        listing.status = "published"
        db.commit()
        db.refresh(listing)

        logger.info(
            f"Listing {listing_id} published to Etsy: etsy_id={listing.etsy_listing_id}"
        )
        return listing

    # ── 조회 ────────────────────────────────────────

    def list_listings(
        self,
        template_id: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
        db: Session = None,
    ) -> dict:
        query = db.query(EtsyListing)
        if template_id:
            query = query.filter(EtsyListing.template_id == template_id)
        if status:
            query = query.filter(EtsyListing.status == status)

        total = query.count()
        listings = (
            query.order_by(EtsyListing.uploaded_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return {"total": total, "listings": listings}

    def get_stats(self, db: Session) -> dict:
        total = db.query(EtsyListing).count()
        published = db.query(EtsyListing).filter(EtsyListing.status == "published").count()
        draft = db.query(EtsyListing).filter(EtsyListing.status == "draft").count()
        avg_price = db.query(func.avg(EtsyListing.price)).scalar() or 0

        return {
            "total_listings": total,
            "published": published,
            "draft": draft,
            "deactivated": total - published - draft,
            "avg_price": round(float(avg_price), 2),
        }

    # ── 직렬화 헬퍼 ─────────────────────────────────

    def listing_to_dict(self, l: EtsyListing, with_template: bool = False) -> dict:
        d = {
            "id": l.id,
            "template_id": l.template_id,
            "pdf_id": l.pdf_id,
            "etsy_listing_id": l.etsy_listing_id,
            "title": l.title,
            "description": l.description,
            "tags": l.tags,
            "price": l.price,
            "status": l.status,
            "views": l.views,
            "favorites": l.favorites,
            "sales": l.sales,
            "uploaded_at": l.uploaded_at.isoformat() if l.uploaded_at else None,
            "updated_at": l.updated_at.isoformat() if l.updated_at else None,
            "etsy_url": (
                f"https://www.etsy.com/listing/{l.etsy_listing_id}"
                if l.etsy_listing_id else None
            ),
        }
        if with_template and l.template:
            d["template_name"] = l.template.name
            d["template_category"] = l.template.category
        return d


# 싱글턴
listing_service = ListingService()
