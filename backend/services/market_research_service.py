"""
Market Research Service - Niche 발견 및 키워드 분석
"""
import logging
from collections import Counter

from sqlalchemy.orm import Session

from ..database import Keyword, Niche
from .etsy_service import etsy_service

logger = logging.getLogger(__name__)

CATEGORY_MAP = {
    "planner": "Planner & Organizer",
    "organizer": "Planner & Organizer",
    "calendar": "Planner & Organizer",
    "resume": "Resume & Career",
    "cv": "Resume & Career",
    "invitation": "Wedding & Events",
    "wedding": "Wedding & Events",
    "party": "Wedding & Events",
    "wall art": "Home Decor",
    "poster": "Home Decor",
    "print": "Home Decor",
    "budget": "Finance & Planner",
    "finance": "Finance & Planner",
    "expense": "Finance & Planner",
    "tracker": "Health & Wellness",
    "habit": "Health & Wellness",
    "sticker": "Stickers & Labels",
    "label": "Stickers & Labels",
    "clipart": "Digital Graphics",
    "svg": "Digital Graphics",
    "logo": "Digital Graphics",
}


class MarketResearchService:
    """
    Etsy 검색 결과를 분석하여 Niche와 Keyword를 DB에 저장하는 서비스.
    """

    async def research_keyword(
        self,
        keyword: str,
        db: Session,
        limit: int = 25,
    ) -> dict:
        """
        키워드 조사 메인 함수.
        1. Etsy API에서 검색 결과 수집
        2. 결과 분석 (가격, 경쟁도, 트렌드)
        3. Niche 및 Keyword DB 저장/업데이트
        4. 분석 결과 반환
        """
        search_result = await etsy_service.search_listings(keyword, limit=limit)
        listings = search_result.get("results", [])

        if not listings:
            return {"error": "No results found", "keyword": keyword}

        analysis = self._analyze_listings(listings)
        niche = self._upsert_niche(keyword, analysis, db)
        extracted_keywords = self._extract_keywords(listings, keyword)
        saved_keywords = self._save_keywords(extracted_keywords, niche.id, db)

        return {
            "niche": self._niche_to_dict(niche),
            "keywords": [self._keyword_to_dict(k) for k in saved_keywords],
            "listings_sample": listings[:5],
            "analysis": analysis,
        }

    def _analyze_listings(self, listings: list) -> dict:
        """
        리스팅 목록에서 통계 지표 계산.
        """
        prices = []
        favorites = []

        for listing in listings:
            if "price" in listing:
                price_data = listing["price"]
                divisor = price_data.get("divisor", 100) or 100
                price = price_data.get("amount", 0) / divisor
                if price > 0:
                    prices.append(price)
            favorites.append(listing.get("num_favorers", 0))

        avg_price = sum(prices) / len(prices) if prices else 0
        avg_favorites = sum(favorites) / len(favorites) if favorites else 0

        if avg_favorites > 1000:
            competition_level = "high"
        elif avg_favorites > 300:
            competition_level = "medium"
        else:
            competition_level = "low"

        max_favorites = max(favorites) if favorites else 1
        trend_score = min(100.0, (avg_favorites / max_favorites) * 100)

        return {
            "avg_price": round(avg_price, 2),
            "price_range": {
                "min": round(min(prices), 2) if prices else 0,
                "max": round(max(prices), 2) if prices else 0,
            },
            "avg_favorites": round(avg_favorites),
            "competition_level": competition_level,
            "trend_score": round(trend_score, 1),
            "search_volume": len(listings) * 100,
        }

    def _upsert_niche(self, keyword: str, analysis: dict, db: Session) -> Niche:
        """Niche 생성 또는 업데이트 (upsert)"""
        competition_score_map = {"low": 0.3, "medium": 0.6, "high": 0.9}
        competition_score = competition_score_map.get(
            analysis["competition_level"], 0.5
        )
        profit_score = self._calc_profit_score(analysis)

        niche = db.query(Niche).filter(Niche.name == keyword).first()

        if niche:
            niche.search_volume = analysis["search_volume"]
            niche.competition_score = competition_score
            niche.avg_price = analysis["avg_price"]
            niche.trend_score = analysis["trend_score"]
            niche.profit_potential_score = profit_score
        else:
            category = self._detect_category(keyword)
            niche = Niche(
                name=keyword,
                category=category,
                search_volume=analysis["search_volume"],
                competition_score=competition_score,
                avg_price=analysis["avg_price"],
                trend_score=analysis["trend_score"],
                profit_potential_score=profit_score,
            )
            db.add(niche)

        db.commit()
        db.refresh(niche)
        return niche

    def _detect_category(self, keyword: str) -> str:
        """키워드에서 카테고리 자동 감지"""
        keyword_lower = keyword.lower()
        for key, category in CATEGORY_MAP.items():
            if key in keyword_lower:
                return category
        return "General"

    def _calc_profit_score(self, analysis: dict) -> float:
        """수익 잠재력 점수 계산 (0-100)"""
        price_score = min(100.0, analysis["avg_price"] * 5)
        competition_penalty_map = {"low": 0, "medium": 20, "high": 40}
        competition_penalty = competition_penalty_map.get(
            analysis["competition_level"], 20
        )
        score = (
            price_score * 0.4
            + analysis["trend_score"] * 0.4
            - competition_penalty * 0.2
        )
        return round(max(0.0, min(100.0, score)), 1)

    def _extract_keywords(self, listings: list, base_keyword: str) -> list:
        """리스팅 태그에서 연관 키워드 추출 (중복 제거, 빈도순 정렬)"""
        tag_counter: Counter = Counter()
        base_lower = base_keyword.lower()

        for listing in listings:
            for tag in listing.get("tags", []):
                tag_lower = tag.lower().strip()
                if tag_lower and tag_lower != base_lower and len(tag_lower) > 2:
                    tag_counter[tag_lower] += 1

        return [tag for tag, _ in tag_counter.most_common(20)]

    def _save_keywords(
        self, keyword_list: list, niche_id: int, db: Session
    ) -> list:
        """키워드 목록을 DB에 저장 (기존 것은 건너뜀)"""
        existing = {
            k.keyword
            for k in db.query(Keyword).filter(Keyword.niche_id == niche_id).all()
        }

        saved = []
        for kw in keyword_list:
            if kw not in existing:
                is_longtail = 1 if len(kw.split()) >= 3 else 0
                kw_obj = Keyword(
                    keyword=kw,
                    niche_id=niche_id,
                    is_longtail=is_longtail,
                    relevance_score=0.5,
                )
                db.add(kw_obj)
                saved.append(kw_obj)

        db.commit()
        return saved

    def _niche_to_dict(self, niche: Niche) -> dict:
        return {
            "id": niche.id,
            "name": niche.name,
            "category": niche.category,
            "search_volume": niche.search_volume,
            "competition_score": niche.competition_score,
            "avg_price": niche.avg_price,
            "trend_score": niche.trend_score,
            "profit_potential_score": niche.profit_potential_score,
            "discovered_at": (
                niche.discovered_at.isoformat() if niche.discovered_at else None
            ),
        }

    def _keyword_to_dict(self, kw: Keyword) -> dict:
        return {
            "id": kw.id,
            "keyword": kw.keyword,
            "niche_id": kw.niche_id,
            "search_volume": kw.search_volume,
            "competition": kw.competition,
            "is_longtail": bool(kw.is_longtail),
            "relevance_score": kw.relevance_score,
        }


# 싱글턴 인스턴스
market_research_service = MarketResearchService()
