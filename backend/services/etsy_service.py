"""
Etsy API Service - Etsy API v3 클라이언트
API 키가 없거나 요청 실패 시 자동으로 Mock 데이터를 반환합니다.
"""
import httpx
import logging
import random
from typing import Optional
from ..config import settings

logger = logging.getLogger(__name__)

ETSY_API_BASE = "https://openapi.etsy.com/v3"

MOCK_TAGS = {
    "planner": ["digital", "printable", "editable", "planner", "organizer", "pdf", "instant download", "template", "weekly", "daily"],
    "resume": ["resume", "cv", "template", "professional", "modern", "editable", "word", "job", "career", "minimalist"],
    "wall art": ["printable", "wall art", "home decor", "digital download", "poster", "artwork", "instant download", "minimalist", "boho", "abstract"],
    "invitation": ["wedding", "invitation", "printable", "editable", "template", "digital", "party", "birthday", "baby shower", "bridal"],
    "budget": ["budget", "finance", "tracker", "spreadsheet", "excel", "google sheets", "money", "savings", "expense", "planner"],
    "sticker": ["sticker", "printable", "planner", "cute", "digital", "kawaii", "label", "clipart", "png", "svg"],
}

DEFAULT_TAGS = ["digital", "printable", "template", "editable", "instant download"]


class EtsyService:
    """
    Etsy API v3 클라이언트.
    API 키가 없거나 요청 실패 시 자동으로 Mock 데이터를 반환합니다.
    """

    def __init__(self):
        self.api_key = settings.etsy_api_key
        self._use_mock = (
            not self.api_key
            or self.api_key == "your_etsy_api_key_here"
        )
        if self._use_mock:
            logger.warning("Etsy API key not configured. Using mock data.")

    async def search_listings(
        self,
        keywords: str,
        limit: int = 25,
        offset: int = 0,
        sort_on: str = "score",
    ) -> dict:
        """
        키워드로 Etsy 리스팅 검색.
        GET /v3/application/listings/active
        """
        if self._use_mock:
            return self._mock_search_results(keywords, limit)

        params = {
            "keywords": keywords,
            "limit": min(limit, 100),
            "offset": offset,
            "sort_on": sort_on,
        }
        headers = {"x-api-key": self.api_key}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{ETSY_API_BASE}/application/listings/active",
                    params=params,
                    headers=headers,
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as e:
            logger.error(f"Etsy search failed: {e}. Falling back to mock data.")
            return self._mock_search_results(keywords, limit)

    async def get_listing_details(self, listing_id: str) -> dict:
        """
        단일 리스팅 상세 조회.
        GET /v3/application/listings/{listing_id}
        """
        if self._use_mock:
            return self._mock_listing_detail(listing_id)

        headers = {"x-api-key": self.api_key}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{ETSY_API_BASE}/application/listings/{listing_id}",
                    headers=headers,
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as e:
            logger.error(f"Etsy listing detail failed: {e}")
            return self._mock_listing_detail(listing_id)

    # ──────────────────────────────────────────
    # Mock 데이터 팩토리
    # ──────────────────────────────────────────

    def _get_tags_for_keyword(self, keyword: str) -> list:
        """키워드 기반 Mock 태그 선택"""
        keyword_lower = keyword.lower()
        for key, tags in MOCK_TAGS.items():
            if key in keyword_lower:
                return tags
        return DEFAULT_TAGS

    def _mock_search_results(self, keywords: str, limit: int) -> dict:
        """개발용 Mock 검색 결과 생성"""
        tags = self._get_tags_for_keyword(keywords)
        results = []

        for i in range(min(limit, 12)):
            price_cents = random.randint(300, 2500)
            num_favorites = random.randint(50, 8000)
            views = random.randint(num_favorites * 3, num_favorites * 20)
            listing_tags = random.sample(tags, k=min(7, len(tags)))

            results.append({
                "listing_id": str(100000000 + i + random.randint(0, 999999)),
                "title": f"{keywords.title()} Template #{i + 1} - Printable & Editable",
                "price": {
                    "amount": price_cents,
                    "divisor": 100,
                    "currency_code": "USD",
                },
                "quantity": random.randint(10, 999),
                "num_favorers": num_favorites,
                "views": views,
                "shop_id": str(10000 + i),
                "seller_name": f"MockShop{i + 1}",
                "tags": listing_tags,
                "images": [
                    {
                        "url_570xN": f"https://picsum.photos/seed/{keywords.replace(' ', '')}{i}/570/570"
                    }
                ],
                "state": "active",
            })

        return {"count": len(results), "results": results}

    def _mock_listing_detail(self, listing_id: str) -> dict:
        """단일 리스팅 Mock 상세 데이터"""
        return {
            "listing_id": listing_id,
            "title": f"Mock Listing #{listing_id}",
            "price": {"amount": 1200, "divisor": 100, "currency_code": "USD"},
            "num_favorers": random.randint(100, 3000),
            "views": random.randint(500, 15000),
            "tags": DEFAULT_TAGS,
            "images": [{"url_570xN": f"https://picsum.photos/seed/{listing_id}/570/570"}],
            "state": "active",
        }

    async def create_draft_listing(
        self,
        title: str,
        description: str,
        tags: list,
        price: float,
        quantity: int = 999,
        listing_type: str = "download",
        shop_id: str = None,
    ) -> dict:
        """
        Etsy에 디지털 다운로드 리스팅 생성 (draft 상태).
        API 미설정 시 Mock 응답 반환.
        POST /v3/application/shops/{shop_id}/listings
        """
        if self._use_mock:
            logger.info("Mock mode: Simulating Etsy listing creation")
            return self._mock_create_listing(title, price)

        if not shop_id:
            logger.warning("No Etsy shop_id configured. Using mock response.")
            return self._mock_create_listing(title, price)

        price_minor = int(round(price * 100))
        payload = {
            "title": title[:140],
            "description": description,
            "price": price_minor,
            "quantity": quantity,
            "tags": tags[:13],
            "who_made": "i_did",
            "when_made": "made_to_order",
            "taxonomy_id": 2078,  # Digital > Templates
            "is_digital": True,
            "state": "draft",
            "type": listing_type,
        }
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(
                    f"{ETSY_API_BASE}/application/shops/{shop_id}/listings",
                    json=payload,
                    headers=headers,
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as e:
            logger.error(f"Etsy create_listing failed: {e}. Returning mock.")
            return self._mock_create_listing(title, price)

    def _mock_create_listing(self, title: str, price: float) -> dict:
        """Mock Etsy listing 생성 응답"""
        mock_id = str(random.randint(900000000, 999999999))
        return {
            "listing_id": mock_id,
            "title": title,
            "price": {"amount": int(price * 100), "divisor": 100, "currency_code": "USD"},
            "state": "draft",
            "is_mock": True,
        }


# 싱글턴 인스턴스
etsy_service = EtsyService()
